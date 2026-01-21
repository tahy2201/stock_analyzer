"""ポートフォリオ管理APIエンドポイント。"""

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.database import models
from app.services.portfolio.portfolio_service import PortfolioService
from app.services.portfolio.position_service import PositionService

router = APIRouter()

# Type aliases
DBSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]


# ========== Pydantic Models ==========


class PortfolioCreateRequest(BaseModel):
    """ポートフォリオ作成のリクエストモデル。"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    initial_capital: float = Field(1000000.00, gt=0)


class PortfolioUpdateRequest(BaseModel):
    """ポートフォリオ更新のリクエストモデル。"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    initial_capital: Optional[float] = Field(None, gt=0)


class PortfolioResponse(BaseModel):
    """ポートフォリオのレスポンスモデル。"""

    id: int
    user_id: int
    name: str
    description: Optional[str]
    initial_capital: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummary(BaseModel):
    """ポートフォリオ一覧のサマリーレスポンスモデル。"""

    id: int
    name: str
    description: Optional[str]
    initial_capital: float
    total_value: float
    total_profit_loss: float
    total_profit_loss_rate: float
    cash_balance: float
    positions_count: int
    created_at: datetime
    updated_at: datetime


class PositionDetail(BaseModel):
    """ポジション詳細のレスポンス。"""

    id: int
    symbol: str
    company_name: Optional[str]
    quantity: int
    average_price: float
    current_price: Optional[float]
    total_cost: float
    current_value: Optional[float]
    profit_loss: Optional[float]
    profit_loss_rate: Optional[float]
    created_at: datetime
    updated_at: datetime


class PortfolioDetail(BaseModel):
    """ポジション情報を含む詳細なポートフォリオレスポンス。"""

    id: int
    name: str
    description: Optional[str]
    initial_capital: float
    total_value: float
    total_profit_loss: float
    total_profit_loss_rate: float
    cash_balance: float
    positions: list[PositionDetail]
    created_at: datetime
    updated_at: datetime


class BuyRequest(BaseModel):
    """銘柄購入のリクエストモデル。"""

    symbol: str = Field(..., min_length=4, max_length=10)
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class SellRequest(BaseModel):
    """銘柄売却のリクエストモデル。"""

    symbol: str = Field(..., min_length=4, max_length=10)
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class DepositRequest(BaseModel):
    """入金のリクエストモデル。"""

    amount: float = Field(..., gt=0)
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class WithdrawalRequest(BaseModel):
    """出金のリクエストモデル。"""

    amount: float = Field(..., gt=0)
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class TransactionResponse(BaseModel):
    """取引のレスポンスモデル。"""

    id: int
    symbol: Optional[str]
    company_name: Optional[str]
    transaction_type: str
    quantity: int
    price: float
    total_amount: float
    profit_loss: Optional[float]
    transaction_date: datetime
    created_at: datetime
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DashboardPortfolioSummary(BaseModel):
    """ダッシュボード用ポートフォリオ概要のレスポンスモデル。"""

    has_portfolio: bool
    positions_count: int
    total_profit_loss: float
    total_profit_loss_rate: float


# ========== Helper Functions ==========


def verify_portfolio_ownership(portfolio_id: int, user_id: int, db: Session) -> models.Portfolio:
    """ポートフォリオがユーザーに属していることを確認する。

    Args:
        portfolio_id: Portfolio ID
        user_id: User ID
        db: Database session

    Returns:
        Portfolio if owned by user

    Raises:
        HTTPException: If portfolio not found or not owned by user
    """
    portfolio: Optional[models.Portfolio] = db.get(models.Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ポートフォリオが見つかりません"
        )
    if portfolio.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このポートフォリオにアクセスする権限がありません",
        )
    return portfolio


# ========== Portfolio Management Endpoints ==========


@router.get("/summary", response_model=DashboardPortfolioSummary)
def get_portfolio_summary(db: DBSession, current_user: CurrentUser):
    """ダッシュボード用のポートフォリオ概要を取得する。

    全ポートフォリオの合計保有銘柄数、総損益、損益率を返す。
    """
    service = PortfolioService(db)
    portfolios = service.get_user_portfolios(current_user.id)

    if not portfolios:
        return DashboardPortfolioSummary(
            has_portfolio=False,
            positions_count=0,
            total_profit_loss=0.0,
            total_profit_loss_rate=0.0,
        )

    total_positions_count = 0
    total_profit_loss = 0.0
    total_initial_capital = 0.0

    for portfolio in portfolios:
        calc = service.calculate_portfolio_value(portfolio.id)
        positions_count = (
            db.query(models.Position).filter(models.Position.portfolio_id == portfolio.id).count()
        )
        total_positions_count += positions_count
        total_profit_loss += calc["total_profit_loss"]
        total_initial_capital += float(portfolio.initial_capital)

    # 総損益率の計算（全ポートフォリオの初期資本に対する割合）
    total_profit_loss_rate = (
        (total_profit_loss / total_initial_capital) * 100 if total_initial_capital > 0 else 0.0
    )

    return DashboardPortfolioSummary(
        has_portfolio=True,
        positions_count=total_positions_count,
        total_profit_loss=total_profit_loss,
        total_profit_loss_rate=total_profit_loss_rate,
    )


@router.get("/", response_model=list[PortfolioSummary])
def get_portfolios(db: DBSession, current_user: CurrentUser):
    """現在のユーザーの全ポートフォリオを取得する。"""
    service = PortfolioService(db)
    portfolios = service.get_user_portfolios(current_user.id)

    result = []
    for portfolio in portfolios:
        # 評価額・損益を計算
        calc = service.calculate_portfolio_value(portfolio.id)

        # ポジション数を取得
        positions_count = (
            db.query(models.Position).filter(models.Position.portfolio_id == portfolio.id).count()
        )

        result.append(
            PortfolioSummary(
                id=portfolio.id,
                name=portfolio.name,
                description=portfolio.description,
                initial_capital=float(portfolio.initial_capital),
                total_value=calc["total_value"],
                total_profit_loss=calc["total_profit_loss"],
                total_profit_loss_rate=calc["total_profit_loss_rate"],
                cash_balance=calc["cash_balance"],
                positions_count=positions_count,
                created_at=portfolio.created_at,
                updated_at=portfolio.updated_at,
            )
        )

    return result


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreateRequest, db: DBSession, current_user: CurrentUser):
    """新しいポートフォリオを作成する。"""
    service = PortfolioService(db)
    portfolio = service.create_portfolio(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        initial_capital=payload.initial_capital,
    )
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio_detail(portfolio_id: int, db: DBSession, current_user: CurrentUser):
    """ポジション情報を含むポートフォリオ詳細を取得する。"""
    # 所有者チェック
    portfolio = verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 評価額・損益を計算
    service = PortfolioService(db)
    calc = service.calculate_portfolio_value(portfolio_id)

    # ポジション一覧取得
    positions = db.query(models.Position).filter(models.Position.portfolio_id == portfolio_id).all()

    position_details = []
    for position in positions:
        # 企業名取得
        company = db.query(models.Company).filter(models.Company.symbol == position.symbol).first()
        company_name = company.name if company else None

        # 最新株価取得
        latest = (
            db.query(models.StockPrice)
            .filter(models.StockPrice.symbol == position.symbol)
            .order_by(models.StockPrice.date.desc())
            .first()
        )
        current_price = float(latest.close) if latest and latest.close else None

        # 評価額・損益計算
        total_cost = float(position.average_price) * position.quantity
        current_value = current_price * position.quantity if current_price else None
        profit_loss = current_value - total_cost if current_value else None
        profit_loss_rate = (profit_loss / total_cost) * 100 if profit_loss and total_cost else None

        position_details.append(
            PositionDetail(
                id=position.id,
                symbol=position.symbol,
                company_name=company_name,
                quantity=position.quantity,
                average_price=float(position.average_price),
                current_price=current_price,
                total_cost=total_cost,
                current_value=current_value,
                profit_loss=profit_loss,
                profit_loss_rate=profit_loss_rate,
                created_at=position.created_at,
                updated_at=position.updated_at,
            )
        )

    return PortfolioDetail(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        initial_capital=float(portfolio.initial_capital),
        total_value=calc["total_value"],
        total_profit_loss=calc["total_profit_loss"],
        total_profit_loss_rate=calc["total_profit_loss_rate"],
        cash_balance=calc["cash_balance"],
        positions=position_details,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int, payload: PortfolioUpdateRequest, db: DBSession, current_user: CurrentUser
):
    """ポートフォリオ情報を更新する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 更新
    service = PortfolioService(db)
    portfolio = service.update_portfolio(
        portfolio_id=portfolio_id,
        name=payload.name,
        description=payload.description,
        initial_capital=payload.initial_capital,
    )
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: int, db: DBSession, current_user: CurrentUser):
    """ポートフォリオを削除する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 削除
    service = PortfolioService(db)
    service.delete_portfolio(portfolio_id)


# ========== Buy/Sell Operations ==========


@router.post("/{portfolio_id}/positions/buy", response_model=TransactionResponse)
def buy_stock(portfolio_id: int, payload: BuyRequest, db: DBSession, current_user: CurrentUser):
    """銘柄を購入する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 購入処理
    service = PositionService(db)
    transaction = service.buy_stock(
        portfolio_id=portfolio_id,
        symbol=payload.symbol,
        quantity=payload.quantity,
        price=payload.price,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
    )

    # 企業名取得
    company = db.query(models.Company).filter(models.Company.symbol == payload.symbol).first()
    company_name = company.name if company else None

    return TransactionResponse(
        id=transaction.id,
        symbol=transaction.symbol,
        company_name=company_name,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price=float(transaction.price),
        total_amount=float(transaction.total_amount),
        profit_loss=float(transaction.profit_loss) if transaction.profit_loss else None,
        transaction_date=transaction.transaction_date,
        created_at=transaction.created_at,
        notes=transaction.notes,
    )


@router.post("/{portfolio_id}/positions/sell", response_model=TransactionResponse)
def sell_stock(portfolio_id: int, payload: SellRequest, db: DBSession, current_user: CurrentUser):
    """銘柄を売却する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 売却処理
    service = PositionService(db)
    transaction = service.sell_stock(
        portfolio_id=portfolio_id,
        symbol=payload.symbol,
        quantity=payload.quantity,
        price=payload.price,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
    )

    # 企業名取得
    company = db.query(models.Company).filter(models.Company.symbol == payload.symbol).first()
    company_name = company.name if company else None

    return TransactionResponse(
        id=transaction.id,
        symbol=transaction.symbol,
        company_name=company_name,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price=float(transaction.price),
        total_amount=float(transaction.total_amount),
        profit_loss=float(transaction.profit_loss) if transaction.profit_loss else None,
        transaction_date=transaction.transaction_date,
        created_at=transaction.created_at,
        notes=transaction.notes,
    )


@router.post("/{portfolio_id}/deposit", response_model=TransactionResponse)
def deposit_cash(
    portfolio_id: int, payload: DepositRequest, db: DBSession, current_user: CurrentUser
):
    """現金を入金する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 入金トランザクション作成
    transaction = models.Transaction(
        portfolio_id=portfolio_id,
        symbol=None,
        transaction_type="deposit",
        quantity=0,
        price=0.0,
        total_amount=payload.amount,
        profit_loss=None,
        transaction_date=payload.transaction_date or datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return TransactionResponse(
        id=transaction.id,
        symbol=None,
        company_name=None,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price=float(transaction.price),
        total_amount=float(transaction.total_amount),
        profit_loss=None,
        transaction_date=transaction.transaction_date,
        created_at=transaction.created_at,
        notes=transaction.notes,
    )


@router.post("/{portfolio_id}/withdraw", response_model=TransactionResponse)
def withdraw_cash(
    portfolio_id: int, payload: WithdrawalRequest, db: DBSession, current_user: CurrentUser
):
    """現金を出金する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # 現金残高チェック
    service = PortfolioService(db)
    calc = service.calculate_portfolio_value(portfolio_id)
    if calc["cash_balance"] < payload.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"現金残高が不足しています（残高: ¥{calc['cash_balance']:,.0f}）",
        )

    # 出金トランザクション作成
    transaction = models.Transaction(
        portfolio_id=portfolio_id,
        symbol=None,
        transaction_type="withdrawal",
        quantity=0,
        price=0.0,
        total_amount=payload.amount,
        profit_loss=None,
        transaction_date=payload.transaction_date or datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return TransactionResponse(
        id=transaction.id,
        symbol=None,
        company_name=None,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price=float(transaction.price),
        total_amount=float(transaction.total_amount),
        profit_loss=None,
        transaction_date=transaction.transaction_date,
        created_at=transaction.created_at,
        notes=transaction.notes,
    )


# ========== Transaction History ==========


@router.get("/{portfolio_id}/transactions", response_model=list[TransactionResponse])
def get_transactions(
    portfolio_id: int,
    db: DBSession,
    current_user: CurrentUser,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    symbol: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
):
    """取引履歴を取得する。"""
    # 所有者チェック
    verify_portfolio_ownership(portfolio_id, current_user.id, db)

    # クエリ構築
    query = db.query(models.Transaction).filter(models.Transaction.portfolio_id == portfolio_id)

    if start_date:
        query = query.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.transaction_date <= end_date)
    if symbol:
        query = query.filter(models.Transaction.symbol == symbol)
    if transaction_type:
        query = query.filter(models.Transaction.transaction_type == transaction_type)

    transactions = query.order_by(models.Transaction.transaction_date.desc()).limit(limit).all()

    # レスポンス構築
    result = []
    for transaction in transactions:
        company = (
            db.query(models.Company).filter(models.Company.symbol == transaction.symbol).first()
        )
        company_name = company.name if company else None

        result.append(
            TransactionResponse(
                id=transaction.id,
                symbol=transaction.symbol,
                company_name=company_name,
                transaction_type=transaction.transaction_type,
                quantity=transaction.quantity,
                price=float(transaction.price),
                total_amount=float(transaction.total_amount),
                profit_loss=float(transaction.profit_loss) if transaction.profit_loss else None,
                transaction_date=transaction.transaction_date,
                created_at=transaction.created_at,
                notes=transaction.notes,
            )
        )

    return result
