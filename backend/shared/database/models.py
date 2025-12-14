"""
SQLAlchemy ORM models for stock analyzer database.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Company(Base):
    """企業基本情報テーブル"""

    __tablename__ = "companies"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revenue: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_enterprise: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    dividend_yield: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class StockPrice(Base):
    """株価データテーブル"""

    __tablename__ = "stock_prices"

    symbol: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.symbol"), primary_key=True
    )
    date: Mapped[datetime] = mapped_column(Date, primary_key=True)
    open: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    high: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    low: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    close: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (Index("idx_stock_prices_symbol_date", "symbol", "date"),)


class TechnicalIndicator(Base):
    """テクニカル指標テーブル"""

    __tablename__ = "technical_indicators"

    symbol: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.symbol"), primary_key=True
    )
    date: Mapped[datetime] = mapped_column(Date, primary_key=True)
    ma_25: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    divergence_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    dividend_yield: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    volume_avg_20: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (Index("idx_technical_indicators_symbol_date", "symbol", "date"),)


class TickerInfo(Base):
    """ティッカー詳細情報テーブル"""

    __tablename__ = "ticker_info"

    symbol: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.symbol"), primary_key=True
    )
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_time_employees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    market_cap: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    current_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    dividend_yield: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    dividend_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    trailing_annual_dividend_rate: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    ex_dividend_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    trailing_pe: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    forward_pe: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    price_to_book: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    return_on_equity: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 6), nullable=True)
    return_on_assets: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 6), nullable=True)
    total_revenue: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    earnings_growth: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 6), nullable=True)
    revenue_growth: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 6), nullable=True)
    profit_margins: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 6), nullable=True)
    fifty_two_week_high: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    fifty_two_week_low: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    average_volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    corporate_actions_dividend: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_ticker_info_symbol", "symbol"),
        Index("idx_ticker_info_last_updated", "last_updated"),
    )


def create_tables() -> None:
    """
    Compatibility function for legacy code.
    This function is kept for backward compatibility but does nothing.
    Database migrations should be managed by Alembic instead.
    """
    pass


if __name__ == "__main__":
    print("Database migrations should be managed by Alembic.")
    print("Please use: alembic upgrade head")
