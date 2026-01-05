"""PortfolioService unit tests."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.database import models
from app.services.portfolio.portfolio_service import PortfolioService


@pytest.fixture
def portfolio_service(db_session):
    """PortfolioServiceのインスタンスを提供。"""
    return PortfolioService(db_session)


@pytest.fixture
def test_user(db_session):
    """テスト用ユーザーを作成。"""
    from app.utils.security import hash_password

    user = models.User(
        login_id="testuser",
        display_name="Test User",
        role="user",
        status="active",
        password_hash=hash_password("Test1234!"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_company(db_session):
    """テスト用企業データを作成。"""
    company = models.Company(
        symbol="1234",
        name="テスト株式会社",
        market="Prime",
        sector="Technology",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_portfolio(db_session, test_user):
    """テスト用ポートフォリオを作成。"""
    portfolio = models.Portfolio(
        user_id=test_user.id,
        name="テストポートフォリオ",
        description="テスト用",
        initial_capital=Decimal("1000000.00"),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_stock_price(db_session, test_company):
    """テスト用株価データを作成。"""
    stock_price = models.StockPrice(
        symbol=test_company.symbol,
        date=datetime.now(timezone.utc),
        open=Decimal("1000.00"),
        high=Decimal("1100.00"),
        low=Decimal("900.00"),
        close=Decimal("1050.00"),
        volume=1000000,
    )
    db_session.add(stock_price)
    db_session.commit()
    db_session.refresh(stock_price)
    return stock_price


class TestCalculatePortfolioValue:
    """calculate_portfolio_value メソッドのテスト。"""

    def test_initial_state(self, portfolio_service, test_portfolio):
        """初期状態（取引なし）のポートフォリオ評価額を計算。"""
        result = portfolio_service.calculate_portfolio_value(test_portfolio.id)

        assert result["total_value"] == 1000000.0
        assert result["cash_balance"] == 1000000.0
        assert result["total_profit_loss"] == 0.0
        assert result["total_profit_loss_rate"] == 0.0

    def test_with_buy_transaction(
        self, portfolio_service, db_session, test_portfolio, test_company, test_stock_price
    ):
        """購入取引後のポートフォリオ評価額を計算。"""
        # 購入取引を作成（100株 x 1000円 = 100,000円）
        transaction = models.Transaction(
            portfolio_id=test_portfolio.id,
            symbol=test_company.symbol,
            transaction_type="buy",
            quantity=100,
            price=Decimal("1000.00"),
            total_amount=Decimal("100000.00"),
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(transaction)

        # ポジションを作成
        position = models.Position(
            portfolio_id=test_portfolio.id,
            symbol=test_company.symbol,
            quantity=100,
            average_price=Decimal("1000.00"),
        )
        db_session.add(position)
        db_session.commit()

        result = portfolio_service.calculate_portfolio_value(test_portfolio.id)

        # 現金残高 = 1,000,000 - 100,000 = 900,000
        assert result["cash_balance"] == 900000.0
        # ポジション評価額 = 100株 x 1,050円（最新株価） = 105,000
        # 総評価額 = 900,000 + 105,000 = 1,005,000
        assert result["total_value"] == 1005000.0
        # 損益 = 1,005,000 - 1,000,000 = 5,000
        assert result["total_profit_loss"] == 5000.0
        # 損益率 = 5,000 / 1,000,000 * 100 = 0.5%
        assert result["total_profit_loss_rate"] == 0.5

    def test_with_deposit_transaction(self, portfolio_service, db_session, test_portfolio):
        """入金取引後のポートフォリオ評価額を計算。"""
        # 入金取引を作成（100,000円）
        transaction = models.Transaction(
            portfolio_id=test_portfolio.id,
            symbol=None,
            transaction_type="deposit",
            quantity=0,
            price=Decimal("0.00"),
            total_amount=Decimal("100000.00"),
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(transaction)
        db_session.commit()

        result = portfolio_service.calculate_portfolio_value(test_portfolio.id)

        # 現金残高 = 1,000,000 + 100,000 = 1,100,000
        assert result["cash_balance"] == 1100000.0
        # 総評価額 = 1,100,000
        assert result["total_value"] == 1100000.0
        # 投資元本 = 1,000,000 + 100,000 = 1,100,000
        # 損益 = 1,100,000 - 1,100,000 = 0（入金は損益に含まれない）
        assert result["total_profit_loss"] == 0.0
        # 損益率 = 0 / 1,100,000 * 100 = 0%
        assert result["total_profit_loss_rate"] == 0.0

    def test_with_withdrawal_transaction(self, portfolio_service, db_session, test_portfolio):
        """出金取引後のポートフォリオ評価額を計算。"""
        # 出金取引を作成（50,000円）
        transaction = models.Transaction(
            portfolio_id=test_portfolio.id,
            symbol=None,
            transaction_type="withdrawal",
            quantity=0,
            price=Decimal("0.00"),
            total_amount=Decimal("50000.00"),
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(transaction)
        db_session.commit()

        result = portfolio_service.calculate_portfolio_value(test_portfolio.id)

        # 現金残高 = 1,000,000 - 50,000 = 950,000
        assert result["cash_balance"] == 950000.0
        # 総評価額 = 950,000
        assert result["total_value"] == 950000.0
        # 投資元本 = 1,000,000 - 50,000 = 950,000
        # 損益 = 950,000 - 950,000 = 0（出金は損益に含まれない）
        assert result["total_profit_loss"] == 0.0
        # 損益率 = 0 / 950,000 * 100 = 0%
        assert result["total_profit_loss_rate"] == 0.0

    def test_with_multiple_transactions(
        self, portfolio_service, db_session, test_portfolio, test_company, test_stock_price
    ):
        """複数の取引（購入、入金、出金）が混在する場合の計算。"""
        # 購入取引（100株 x 1000円 = 100,000円）
        buy_transaction = models.Transaction(
            portfolio_id=test_portfolio.id,
            symbol=test_company.symbol,
            transaction_type="buy",
            quantity=100,
            price=Decimal("1000.00"),
            total_amount=Decimal("100000.00"),
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(buy_transaction)

        # ポジション作成
        position = models.Position(
            portfolio_id=test_portfolio.id,
            symbol=test_company.symbol,
            quantity=100,
            average_price=Decimal("1000.00"),
        )
        db_session.add(position)

        # 入金取引（200,000円）
        deposit_transaction = models.Transaction(
            portfolio_id=test_portfolio.id,
            symbol=None,
            transaction_type="deposit",
            quantity=0,
            price=Decimal("0.00"),
            total_amount=Decimal("200000.00"),
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(deposit_transaction)

        # 出金取引（50,000円）
        withdrawal_transaction = models.Transaction(
            portfolio_id=test_portfolio.id,
            symbol=None,
            transaction_type="withdrawal",
            quantity=0,
            price=Decimal("0.00"),
            total_amount=Decimal("50000.00"),
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(withdrawal_transaction)
        db_session.commit()

        result = portfolio_service.calculate_portfolio_value(test_portfolio.id)

        # 現金残高 = 1,000,000 - 100,000（購入） + 200,000（入金） - 50,000（出金） = 1,050,000
        assert result["cash_balance"] == 1050000.0
        # ポジション評価額 = 100株 x 1,050円 = 105,000
        # 総評価額 = 1,050,000 + 105,000 = 1,155,000
        assert result["total_value"] == 1155000.0
        # 投資元本 = 1,000,000 + 200,000（入金） - 50,000（出金） = 1,150,000
        # 損益 = 1,155,000 - 1,150,000 = 5,000（株の評価益のみ）
        assert result["total_profit_loss"] == 5000.0
        # 損益率 = 5,000 / 1,150,000 * 100 ≈ 0.43%
        assert abs(result["total_profit_loss_rate"] - 0.43478260869565216) < 0.0001
