import datetime
from typing import Any, Optional, cast

import pandas as pd

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.database.database_manager import DatabaseManager

router = APIRouter()

# レスポンスモデル
class StockPrice(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class StockInfo(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    current_price: Optional[float] = None
    dividend_yield: Optional[float] = None

class TechnicalIndicator(BaseModel):
    date: str
    ma_25: Optional[float] = None
    divergence_rate: Optional[float] = None
    volume_avg_20: Optional[int] = None

class TickerInfo(BaseModel):
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    debt_to_equity: Optional[float] = None
    market_cap: Optional[int] = None
    total_revenue: Optional[int] = None
    earnings_growth: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_margins: Optional[float] = None
    dividend_rate: Optional[float] = None
    trailing_annual_dividend_rate: Optional[float] = None
    ex_dividend_date: Optional[str] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    average_volume: Optional[int] = None

class StockDetail(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    current_price: Optional[float] = None
    price_change: Optional[float] = None  # 前日比（金額）
    price_change_percent: Optional[float] = None  # 前日比（%）
    dividend_yield: Optional[float] = None
    prices: list[StockPrice] = Field(default_factory=list)
    technical_indicators: list[TechnicalIndicator] = Field(default_factory=list)
    ticker_info: Optional[TickerInfo] = None

# データベースマネージャー
db_manager = DatabaseManager()

@router.get("/", response_model=list[StockInfo])
async def get_stocks(limit: int = 100):
    """全株式リストを取得"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT c.symbol, c.name, c.sector, c.market
                FROM companies c
                ORDER BY c.symbol
                LIMIT ?
            """, (limit,))

            stocks = []
            for row in cursor.fetchall():
                stocks.append(StockInfo(
                    symbol=row["symbol"],
                    name=row["name"],
                    sector=row["sector"],
                    market=row["market"]
                ))

            return stocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/{symbol}", response_model=StockDetail)
async def get_stock_detail(symbol: str, days: int = 365):
    """個別銘柄の詳細情報を取得"""
    try:
        # 企業情報取得
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, name, sector, market, dividend_yield
                FROM companies
                WHERE symbol = ?
            """, (symbol,))

            company = cursor.fetchone()
            if not company:
                raise HTTPException(status_code=404, detail="銘柄が見つかりません")

        # 株価データ取得
        price_data = db_manager.get_stock_prices(symbol)

        prices = []
        current_price = None
        price_change = None
        price_change_percent = None

        if not price_data.empty:
            # 最新の指定日数分のデータを取得
            recent_data = price_data.tail(days)
            current_price = float(recent_data["close"].iloc[-1])

            # 前日比計算
            if len(recent_data) >= 2:
                previous_price = float(recent_data["close"].iloc[-2])
                price_change = current_price - previous_price
                price_change_percent = (price_change / previous_price) * 100

            for date, row in recent_data.iterrows():
                if isinstance(date, (pd.Timestamp, datetime.datetime, datetime.date)):
                    date_ts = date
                else:
                    date_ts = pd.to_datetime(str(date))
                prices.append(StockPrice(
                    date=date_ts.strftime("%Y-%m-%d"),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"])
                ))

        # テクニカル指標取得
        technical_data = db_manager.get_technical_indicators(symbol)
        technical_indicators = []

        if not technical_data.empty:
            recent_technical = technical_data.tail(days)
            for date, row in recent_technical.iterrows():
                if isinstance(date, (pd.Timestamp, datetime.datetime, datetime.date)):
                    date_ts = date
                else:
                    date_ts = pd.to_datetime(str(date))
                technical_indicators.append(TechnicalIndicator(
                    date=date_ts.strftime("%Y-%m-%d"),
                    ma_25=float(row["ma_25"]) if row["ma_25"] is not None else None,
                    divergence_rate=float(row["divergence_rate"]) if row["divergence_rate"] is not None else None,
                    volume_avg_20=int(row["volume_avg_20"]) if row["volume_avg_20"] is not None else None
                ))

        # ティッカー情報取得
        ticker_data = db_manager.get_ticker_info(symbol)
        ticker_info = None

        if ticker_data:
            ticker_info = TickerInfo(
                trailing_pe=ticker_data.get("trailing_pe"),
                forward_pe=ticker_data.get("forward_pe"),
                price_to_book=ticker_data.get("price_to_book"),
                return_on_equity=ticker_data.get("return_on_equity"),
                return_on_assets=ticker_data.get("return_on_assets"),
                debt_to_equity=ticker_data.get("debt_to_equity"),
                market_cap=ticker_data.get("market_cap"),
                total_revenue=ticker_data.get("total_revenue"),
                earnings_growth=ticker_data.get("earnings_growth"),
                revenue_growth=ticker_data.get("revenue_growth"),
                profit_margins=ticker_data.get("profit_margins"),
                dividend_rate=ticker_data.get("dividend_rate"),
                trailing_annual_dividend_rate=ticker_data.get("trailing_annual_dividend_rate"),
                ex_dividend_date=str(ticker_data.get("ex_dividend_date")) if ticker_data.get("ex_dividend_date") else None,
                fifty_two_week_high=ticker_data.get("fifty_two_week_high"),
                fifty_two_week_low=ticker_data.get("fifty_two_week_low"),
                average_volume=ticker_data.get("average_volume")
            )

        # 動的配当利回り計算
        dividend_yield = None
        if current_price:
            from services.analysis.technical_analyzer import TechnicalAnalyzer
            analyzer = TechnicalAnalyzer()
            dividend_yield = analyzer.get_dividend_yield(symbol, current_price)

        return StockDetail(
            symbol=company["symbol"],
            name=company["name"],
            sector=company["sector"],
            market=company["market"],
            current_price=current_price,
            price_change=price_change,
            price_change_percent=price_change_percent,
            dividend_yield=dividend_yield,
            prices=prices,
            technical_indicators=technical_indicators,
            ticker_info=ticker_info
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/{symbol}/prices", response_model=list[StockPrice])
async def get_stock_prices(symbol: str, days: int = 100):
    """銘柄の株価データのみを取得"""
    try:
        price_data = db_manager.get_stock_prices(symbol)

        if price_data.empty:
            raise HTTPException(status_code=404, detail="株価データが見つかりません")

        # 最新の指定日数分のデータを取得
        recent_data = price_data.tail(days)

        prices = []
        for date, row in recent_data.iterrows():
            if isinstance(date, (pd.Timestamp, datetime.datetime, datetime.date)):
                date_ts = date
            else:
                date_ts = pd.to_datetime(str(date))
            prices.append(StockPrice(
                date=date_ts.strftime("%Y-%m-%d"),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"])
            ))

        return prices

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
