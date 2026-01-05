"""ポートフォリオのポジション（売買操作）を管理するサービス。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database import models


class PositionService:
    """銘柄のポジションと取引を管理するサービス。"""

    def __init__(self, db: Session):
        """ポジションサービスを初期化する。

        Args:
            db: SQLAlchemyデータベースセッション
        """
        self.db = db

    def buy_stock(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: int,
        price: Optional[float],
        transaction_date: Optional[datetime],
        notes: Optional[str],
    ) -> models.Transaction:
        """銘柄を購入してポジションを更新する。

        Args:
            portfolio_id: ポートフォリオID
            symbol: 銘柄コード
            quantity: 購入株数
            price: 1株あたりの購入価格（Noneの場合は最新株価を使用）
            transaction_date: 取引日時（Noneの場合は現在時刻）
            notes: 取引メモ（オプション）

        Returns:
            作成された取引記録

        Raises:
            HTTPException: 株価データが見つからない場合
        """
        # price未指定時は最新終値を取得
        if not price:
            price = self._get_latest_price(symbol)

        # 既存ポジション取得
        position = (
            self.db.query(models.Position)
            .filter(models.Position.portfolio_id == portfolio_id, models.Position.symbol == symbol)
            .first()
        )

        if position:
            # 加重平均計算
            total_cost = float(position.average_price) * position.quantity + price * quantity
            total_quantity = position.quantity + quantity
            position.average_price = total_cost / total_quantity
            position.quantity = total_quantity
        else:
            # 新規ポジション作成
            position = models.Position(
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=quantity,
                average_price=price,
            )
            self.db.add(position)

        # トランザクション記録
        transaction = models.Transaction(
            portfolio_id=portfolio_id,
            symbol=symbol,
            transaction_type="buy",
            quantity=quantity,
            price=price,
            total_amount=price * quantity,
            transaction_date=transaction_date or datetime.now(timezone.utc),
            notes=notes,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def sell_stock(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: int,
        price: Optional[float],
        transaction_date: Optional[datetime],
        notes: Optional[str],
    ) -> models.Transaction:
        """銘柄を売却してポジションを更新する。

        Args:
            portfolio_id: ポートフォリオID
            symbol: 銘柄コード
            quantity: 売却株数
            price: 1株あたりの売却価格（Noneの場合は最新株価を使用）
            transaction_date: 取引日時（Noneの場合は現在時刻）
            notes: 取引メモ（オプション）

        Returns:
            作成された取引記録

        Raises:
            HTTPException: 保有株数が不足している場合、または株価データが見つからない場合
        """
        # 保有チェック
        position = (
            self.db.query(models.Position)
            .filter(models.Position.portfolio_id == portfolio_id, models.Position.symbol == symbol)
            .first()
        )

        if not position or position.quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="売却可能な株数が不足しています"
            )

        # price未指定時は最新終値
        if not price:
            price = self._get_latest_price(symbol)

        # 損益計算
        profit_loss = (price - float(position.average_price)) * quantity

        # ポジション更新
        position.quantity -= quantity
        if position.quantity == 0:
            self.db.delete(position)

        # トランザクション記録
        transaction = models.Transaction(
            portfolio_id=portfolio_id,
            symbol=symbol,
            transaction_type="sell",
            quantity=quantity,
            price=price,
            total_amount=price * quantity,
            profit_loss=profit_loss,
            transaction_date=transaction_date or datetime.now(timezone.utc),
            notes=notes,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def _get_latest_price(self, symbol: str) -> float:
        """stock_pricesテーブルから最新の株価を取得する。

        Args:
            symbol: 銘柄コード

        Returns:
            最新の終値

        Raises:
            HTTPException: 株価データが見つからない場合
        """
        latest = (
            self.db.query(models.StockPrice)
            .filter(models.StockPrice.symbol == symbol)
            .order_by(models.StockPrice.date.desc())
            .first()
        )

        if not latest or not latest.close:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"銘柄 {symbol} の株価データが見つかりません",
            )

        return float(latest.close)
