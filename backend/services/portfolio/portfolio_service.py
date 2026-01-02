"""ポートフォリオのCRUD操作を行うサービス。"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from shared.database import models


class PortfolioService:
    """ポートフォリオを管理するサービス。"""

    def __init__(self, db: Session):
        """ポートフォリオサービスを初期化する。

        Args:
            db: SQLAlchemyデータベースセッション
        """
        self.db = db

    def create_portfolio(
        self, user_id: int, name: str, description: Optional[str], initial_capital: float
    ) -> models.Portfolio:
        """新しいポートフォリオを作成する。

        Args:
            user_id: ユーザーID
            name: ポートフォリオ名
            description: 説明（オプション）
            initial_capital: 初期資本金

        Returns:
            作成されたポートフォリオ

        Raises:
            HTTPException: ユーザーが既に10個のポートフォリオを持っている場合
        """
        # ユーザーあたり最大10個チェック
        count = (
            self.db.query(models.Portfolio)
            .filter(models.Portfolio.user_id == user_id)
            .count()
        )
        if count >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ポートフォリオは最大10個までです",
            )

        # 作成処理
        portfolio = models.Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            initial_capital=initial_capital,
        )
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)

        return portfolio

    def get_user_portfolios(self, user_id: int) -> list[models.Portfolio]:
        """ユーザーの全ポートフォリオを取得する。

        Args:
            user_id: ユーザーID

        Returns:
            ポートフォリオのリスト
        """
        portfolios: list[models.Portfolio] = (
            self.db.query(models.Portfolio)
            .filter(models.Portfolio.user_id == user_id)
            .all()
        )
        return portfolios

    def get_portfolio_by_id(self, portfolio_id: int) -> Optional[models.Portfolio]:
        """IDでポートフォリオを取得する。

        Args:
            portfolio_id: ポートフォリオID

        Returns:
            ポートフォリオ、見つからない場合はNone
        """
        portfolio: Optional[models.Portfolio] = self.db.get(models.Portfolio, portfolio_id)
        return portfolio

    def update_portfolio(
        self,
        portfolio_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        initial_capital: Optional[float] = None,
    ) -> models.Portfolio:
        """ポートフォリオ情報を更新する。

        Args:
            portfolio_id: ポートフォリオID
            name: 新しい名前（オプション）
            description: 新しい説明（オプション）
            initial_capital: 新しい初期資本金（オプション）

        Returns:
            更新されたポートフォリオ

        Raises:
            HTTPException: ポートフォリオが見つからない場合
        """
        portfolio: Optional[models.Portfolio] = self.db.get(models.Portfolio, portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="ポートフォリオが見つかりません"
            )

        if name is not None:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        if initial_capital is not None:
            portfolio.initial_capital = initial_capital

        self.db.commit()
        self.db.refresh(portfolio)

        return portfolio

    def delete_portfolio(self, portfolio_id: int) -> None:
        """ポートフォリオを削除する。

        Args:
            portfolio_id: ポートフォリオID

        Raises:
            HTTPException: ポートフォリオが見つからない場合
        """
        portfolio = self.db.get(models.Portfolio, portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="ポートフォリオが見つかりません"
            )

        self.db.delete(portfolio)
        self.db.commit()

    def calculate_portfolio_value(self, portfolio_id: int) -> dict:
        """ポートフォリオの総評価額と損益を計算する。

        Args:
            portfolio_id: ポートフォリオID

        Returns:
            total_value、total_profit_loss等を含む辞書
        """
        portfolio = self.db.get(models.Portfolio, portfolio_id)
        if not portfolio:
            return {
                "total_value": 0.0,
                "total_profit_loss": 0.0,
                "total_profit_loss_rate": 0.0,
                "cash_balance": 0.0,
            }

        # ポジション一覧取得
        positions = (
            self.db.query(models.Position)
            .filter(models.Position.portfolio_id == portfolio_id)
            .all()
        )

        # 各銘柄の評価額計算
        total_position_value = 0.0
        for position in positions:
            # 最新株価取得
            latest = (
                self.db.query(models.StockPrice)
                .filter(models.StockPrice.symbol == position.symbol)
                .order_by(models.StockPrice.date.desc())
                .first()
            )
            if latest and latest.close:
                current_price = float(latest.close)
                position_value = current_price * position.quantity
                total_position_value += position_value

        # 総購入額、総売却額、入金額、出金額を計算
        transactions = (
            self.db.query(models.Transaction)
            .filter(models.Transaction.portfolio_id == portfolio_id)
            .all()
        )
        total_buy_amount = sum(
            float(t.total_amount) for t in transactions if t.transaction_type == "buy"
        )
        total_sell_amount = sum(
            float(t.total_amount) for t in transactions if t.transaction_type == "sell"
        )
        total_deposit = sum(
            float(t.total_amount) for t in transactions if t.transaction_type == "deposit"
        )
        total_withdrawal = sum(
            float(t.total_amount) for t in transactions if t.transaction_type == "withdrawal"
        )

        # 現金残高 = 初期資本 - 総購入額 + 総売却額 + 入金額 - 出金額
        cash_balance = (
            float(portfolio.initial_capital)
            - total_buy_amount
            + total_sell_amount
            + total_deposit
            - total_withdrawal
        )

        # 総評価額 = 現在のポジション評価額 + 現金残高
        total_value = total_position_value + cash_balance

        # 総損益 = 総評価額 - 初期資本
        total_profit_loss = total_value - float(portfolio.initial_capital)

        # 損益率 = (総損益 / 初期資本) * 100
        total_profit_loss_rate = (
            (total_profit_loss / float(portfolio.initial_capital)) * 100
            if portfolio.initial_capital != 0
            else 0.0
        )

        return {
            "total_value": total_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_rate": total_profit_loss_rate,
            "cash_balance": cash_balance,
        }
