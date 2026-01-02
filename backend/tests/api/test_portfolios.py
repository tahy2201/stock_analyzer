"""Portfolio API endpoint tests."""

import pytest
import pytest_asyncio
from decimal import Decimal


@pytest.fixture
def test_user(create_user):
    """テスト用ユーザーを作成するフィクスチャ。"""
    return create_user(login_id="testuser", password="Test1234!", role="user", status="active")


@pytest_asyncio.fixture
async def authenticated_client(client, test_user):
    """認証済みクライアントセッションを作成するフィクスチャ。"""
    await client.post("/api/auth/login", json={"login_id": "testuser", "password": "Test1234!"})
    return client


@pytest.fixture
def another_user(create_user):
    """別の認証済みユーザーを作成（所有者チェック用）。"""
    return create_user(login_id="otheruser", password="Other1234!", role="user", status="active")


@pytest.fixture
def create_company(db_session):
    """テスト用企業データを作成するヘルパー。"""
    from shared.database import models

    def _create_company(symbol: str, name: str):
        company = models.Company(
            symbol=symbol,
            name=name,
            market="Prime",
            sector="Technology",
        )
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)
        return company

    return _create_company


@pytest.fixture
def create_stock_price(db_session):
    """テスト用株価データを作成するヘルパー。"""
    from datetime import datetime
    from shared.database import models

    def _create_stock_price(symbol: str, close: float, date: datetime | None = None):
        from datetime import datetime

        stock_price = models.StockPrice(
            symbol=symbol,
            date=date or datetime.now(),
            open=Decimal(str(close)),
            high=Decimal(str(close)),
            low=Decimal(str(close)),
            close=Decimal(str(close)),
            volume=1000000,
        )
        db_session.add(stock_price)
        db_session.commit()
        db_session.refresh(stock_price)
        return stock_price

    return _create_stock_price


# ========== ポートフォリオCRUD操作 ==========


@pytest.mark.asyncio
async def test_create_portfolio_success(authenticated_client, test_user):
    """ポートフォリオ作成のテスト。"""
    res = await authenticated_client.post(
        "/api/portfolios/",
        json={
            "name": "テストポートフォリオ",
            "description": "テスト用のポートフォリオです",
            "initial_capital": 1000000.0,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "テストポートフォリオ"
    assert data["description"] == "テスト用のポートフォリオです"
    assert data["initial_capital"] == 1000000.0
    assert data["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_create_portfolio_without_auth(client):
    """認証なしでポートフォリオ作成を試みる（失敗すべき）。"""
    res = await client.post(
        "/api/portfolios/",
        json={
            "name": "テストポートフォリオ",
            "initial_capital": 1000000.0,
        },
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_portfolios_list(authenticated_client, test_user, db_session):
    """ポートフォリオ一覧取得のテスト。"""
    from shared.database import models

    # テストデータ作成
    portfolio1 = models.Portfolio(
        user_id=test_user.id,
        name="Portfolio 1",
        initial_capital=Decimal("1000000.00"),
    )
    portfolio2 = models.Portfolio(
        user_id=test_user.id,
        name="Portfolio 2",
        initial_capital=Decimal("2000000.00"),
    )
    db_session.add_all([portfolio1, portfolio2])
    db_session.commit()

    # 一覧取得
    res = await authenticated_client.get("/api/portfolios/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["name"] == "Portfolio 1"
    assert data[1]["name"] == "Portfolio 2"


@pytest.mark.asyncio
async def test_cannot_access_other_user_portfolio(authenticated_client, another_user, db_session):
    """他人のポートフォリオにアクセスできないことを確認。"""
    from shared.database import models

    # 別ユーザーのポートフォリオ作成
    other_portfolio = models.Portfolio(
        user_id=another_user.id,
        name="Other User's Portfolio",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(other_portfolio)
    db_session.commit()
    db_session.refresh(other_portfolio)

    # アクセス試行（403エラーが返るべき）
    res = await authenticated_client.get(f"/api/portfolios/{other_portfolio.id}")
    assert res.status_code == 403
    assert "権限がありません" in res.json()["detail"]


# ========== 銘柄売買 ==========


@pytest.mark.asyncio
async def test_buy_stock_success(
    authenticated_client, test_user, db_session, create_company, create_stock_price
):
    """銘柄購入のテスト。"""
    from shared.database import models

    # テスト用企業と株価作成
    create_company(symbol="7203", name="トヨタ自動車")
    create_stock_price(symbol="7203", close=3000.0)

    # ポートフォリオ作成
    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 銘柄購入
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={
            "symbol": "7203",
            "quantity": 100,
            "price": 3000.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "7203"
    assert data["transaction_type"] == "buy"
    assert data["quantity"] == 100
    assert data["price"] == 3000.0
    assert data["total_amount"] == 300000.0

    # ポジション確認
    position = (
        db_session.query(models.Position)
        .filter(models.Position.portfolio_id == portfolio.id, models.Position.symbol == "7203")
        .first()
    )
    assert position is not None
    assert position.quantity == 100
    assert float(position.average_price) == 3000.0


@pytest.mark.asyncio
async def test_buy_stock_multiple_times_weighted_average(
    authenticated_client, test_user, db_session, create_company, create_stock_price
):
    """同じ銘柄を複数回購入して加重平均を確認。"""
    from shared.database import models

    create_company(symbol="7203", name="トヨタ自動車")
    create_stock_price(symbol="7203", close=3000.0)

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_capital=Decimal("10000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 1回目の購入: 100株 @ 3000円
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={"symbol": "7203", "quantity": 100, "price": 3000.0},
    )

    # 2回目の購入: 50株 @ 3300円
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={"symbol": "7203", "quantity": 50, "price": 3300.0},
    )

    # ポジション確認
    position = (
        db_session.query(models.Position)
        .filter(models.Position.portfolio_id == portfolio.id, models.Position.symbol == "7203")
        .first()
    )
    assert position.quantity == 150

    # 加重平均: (100 * 3000 + 50 * 3300) / 150 = 3100
    expected_avg = (100 * 3000 + 50 * 3300) / 150
    assert abs(float(position.average_price) - expected_avg) < 0.01


@pytest.mark.asyncio
async def test_sell_stock_success(
    authenticated_client, test_user, db_session, create_company, create_stock_price
):
    """銘柄売却のテスト。"""
    from shared.database import models

    create_company(symbol="7203", name="トヨタ自動車")
    create_stock_price(symbol="7203", close=3000.0)

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # まず購入
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={"symbol": "7203", "quantity": 100, "price": 3000.0},
    )

    # 売却
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/sell",
        json={"symbol": "7203", "quantity": 50, "price": 3500.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "7203"
    assert data["transaction_type"] == "sell"
    assert data["quantity"] == 50
    assert data["price"] == 3500.0

    # 損益確認: (3500 - 3000) * 50 = 25000
    assert data["profit_loss"] == 25000.0

    # ポジション確認（50株残る）
    position = (
        db_session.query(models.Position)
        .filter(models.Position.portfolio_id == portfolio.id, models.Position.symbol == "7203")
        .first()
    )
    assert position.quantity == 50


@pytest.mark.asyncio
async def test_sell_stock_all_shares(
    authenticated_client, test_user, db_session, create_company, create_stock_price
):
    """全株売却でポジションが削除されることを確認。"""
    from shared.database import models

    create_company(symbol="7203", name="トヨタ自動車")
    create_stock_price(symbol="7203", close=3000.0)

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 購入
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={"symbol": "7203", "quantity": 100, "price": 3000.0},
    )

    # 全株売却
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/sell",
        json={"symbol": "7203", "quantity": 100, "price": 3200.0},
    )

    # ポジション削除確認
    position = (
        db_session.query(models.Position)
        .filter(models.Position.portfolio_id == portfolio.id, models.Position.symbol == "7203")
        .first()
    )
    assert position is None


@pytest.mark.asyncio
async def test_sell_stock_insufficient_shares(
    authenticated_client, test_user, db_session, create_company, create_stock_price
):
    """保有株数不足で売却できないことを確認。"""
    from shared.database import models

    create_company(symbol="7203", name="トヨタ自動車")
    create_stock_price(symbol="7203", close=3000.0)

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 100株購入
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={"symbol": "7203", "quantity": 100, "price": 3000.0},
    )

    # 150株売却を試みる（失敗すべき）
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/sell",
        json={"symbol": "7203", "quantity": 150, "price": 3200.0},
    )
    assert res.status_code == 400
    assert "不足" in res.json()["detail"]


# ========== 取引履歴 ==========


@pytest.mark.asyncio
async def test_get_transactions(
    authenticated_client, test_user, db_session, create_company, create_stock_price
):
    """取引履歴取得のテスト。"""
    from shared.database import models

    create_company(symbol="7203", name="トヨタ自動車")
    create_stock_price(symbol="7203", close=3000.0)

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 購入・売却を実行
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/buy",
        json={"symbol": "7203", "quantity": 100, "price": 3000.0},
    )
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/positions/sell",
        json={"symbol": "7203", "quantity": 50, "price": 3500.0},
    )

    # 履歴取得
    res = await authenticated_client.get(f"/api/portfolios/{portfolio.id}/transactions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2

    # 降順（新しい順）
    assert data[0]["transaction_type"] == "sell"
    assert data[1]["transaction_type"] == "buy"


# ========== 入金・出金操作 ==========


@pytest.mark.asyncio
async def test_deposit_cash_success(authenticated_client, test_user, db_session):
    """現金入金のテスト。"""
    # ポートフォリオ作成
    from shared.database import models

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="入金テスト",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 入金実行
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/deposit",
        json={"amount": 100000.0, "notes": "テスト入金"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["transaction_type"] == "deposit"
    assert data["total_amount"] == 100000.0
    assert data["symbol"] is None
    assert data["notes"] == "テスト入金"

    # ポートフォリオ詳細を確認
    res = await authenticated_client.get(f"/api/portfolios/{portfolio.id}")
    assert res.status_code == 200
    data = res.json()
    # 現金残高 = 1,000,000 + 100,000 = 1,100,000
    assert data["cash_balance"] == 1100000.0
    assert data["total_value"] == 1100000.0


@pytest.mark.asyncio
async def test_withdraw_cash_success(authenticated_client, test_user, db_session):
    """現金出金のテスト。"""
    # ポートフォリオ作成
    from shared.database import models

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="出金テスト",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 出金実行
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/withdraw",
        json={"amount": 50000.0, "notes": "テスト出金"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["transaction_type"] == "withdrawal"
    assert data["total_amount"] == 50000.0
    assert data["symbol"] is None
    assert data["notes"] == "テスト出金"

    # ポートフォリオ詳細を確認
    res = await authenticated_client.get(f"/api/portfolios/{portfolio.id}")
    assert res.status_code == 200
    data = res.json()
    # 現金残高 = 1,000,000 - 50,000 = 950,000
    assert data["cash_balance"] == 950000.0
    assert data["total_value"] == 950000.0


@pytest.mark.asyncio
async def test_withdraw_cash_insufficient_balance(authenticated_client, test_user, db_session):
    """現金残高不足での出金失敗テスト。"""
    # ポートフォリオ作成
    from shared.database import models

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="残高不足テスト",
        initial_capital=Decimal("100000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 残高以上の出金を試みる
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/withdraw",
        json={"amount": 200000.0},
    )
    assert res.status_code == 400
    data = res.json()
    assert "現金残高が不足しています" in data["detail"]


@pytest.mark.asyncio
async def test_deposit_without_auth(client, test_user, db_session):
    """認証なしでの入金失敗テスト。"""
    from shared.database import models

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="認証なしテスト",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    res = await client.post(
        f"/api/portfolios/{portfolio.id}/deposit",
        json={"amount": 100000.0},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_withdraw_unauthorized_portfolio(authenticated_client, test_user, another_user, db_session):
    """他人のポートフォリオへの出金失敗テスト。"""
    from shared.database import models

    # 別ユーザーのポートフォリオを作成
    portfolio = models.Portfolio(
        user_id=another_user.id,
        name="他人のポートフォリオ",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 出金を試みる
    res = await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/withdraw",
        json={"amount": 50000.0},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_deposit_and_withdraw_in_transactions(authenticated_client, test_user, db_session):
    """入金・出金が取引履歴に記録されることを確認。"""
    from shared.database import models

    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="履歴テスト",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    # 入金
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/deposit",
        json={"amount": 100000.0},
    )

    # 出金
    await authenticated_client.post(
        f"/api/portfolios/{portfolio.id}/withdraw",
        json={"amount": 30000.0},
    )

    # 取引履歴を確認
    res = await authenticated_client.get(f"/api/portfolios/{portfolio.id}/transactions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    
    # 降順（新しい順）で確認
    assert data[0]["transaction_type"] == "withdrawal"
    assert data[0]["total_amount"] == 30000.0
    assert data[1]["transaction_type"] == "deposit"
    assert data[1]["total_amount"] == 100000.0
