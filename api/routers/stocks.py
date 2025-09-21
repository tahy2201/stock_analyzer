from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.database_manager import DatabaseManager

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

class StockDetail(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    current_price: Optional[float] = None
    dividend_yield: Optional[float] = None
    prices: List[StockPrice] = []

# データベースマネージャー
db_manager = DatabaseManager()

@router.get("/", response_model=List[StockInfo])
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}", response_model=StockDetail)
async def get_stock_detail(symbol: str, days: int = 100):
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

        if not price_data.empty:
            # 最新の指定日数分のデータを取得
            recent_data = price_data.tail(days)
            current_price = float(recent_data["close"].iloc[-1])

            for date, row in recent_data.iterrows():
                prices.append(StockPrice(
                    date=date.strftime("%Y-%m-%d"),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"])
                ))

        # 動的配当利回り計算
        dividend_yield = None
        if current_price:
            from batch.technical_analyzer import TechnicalAnalyzer
            analyzer = TechnicalAnalyzer()
            dividend_yield = analyzer.get_dividend_yield(symbol, current_price)

        return StockDetail(
            symbol=company["symbol"],
            name=company["name"],
            sector=company["sector"],
            market=company["market"],
            current_price=current_price,
            dividend_yield=dividend_yield,
            prices=prices
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/prices", response_model=List[StockPrice])
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
            prices.append(StockPrice(
                date=date.strftime("%Y-%m-%d"),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"])
            ))

        return prices

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))