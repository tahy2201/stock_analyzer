from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database.database_manager import DatabaseManager
from app.services.analysis.technical_analyzer_service import TechnicalAnalyzerService

router = APIRouter()


# レスポンスモデル
class TechnicalAnalysis(BaseModel):
    symbol: str
    current_price: Optional[float] = None
    ma_25: Optional[float] = None
    divergence_rate: Optional[float] = None
    dividend_yield: Optional[float] = None
    volume_avg_20: Optional[float] = None
    ma_trend: Optional[str] = None
    price_trend: Optional[str] = None
    last_updated: Optional[str] = None


class SystemStats(BaseModel):
    """システム統計情報のレスポンスモデル。"""

    symbols_with_prices: int
    latest_price_date: Optional[str] = None
    market_filter: Optional[str] = None


@router.get("/{symbol}", response_model=TechnicalAnalysis)
async def get_technical_analysis(symbol: str):
    """個別銘柄の技術分析を取得"""
    try:
        analyzer = TechnicalAnalyzerService()

        # 技術分析サマリーを取得
        summary = analyzer.get_technical_summary(symbol)

        if not summary:
            raise HTTPException(status_code=404, detail="技術分析データが見つかりません")

        last_updated_raw = summary.get("last_updated")
        last_updated = (
            last_updated_raw.strftime("%Y-%m-%d")
            if isinstance(last_updated_raw, datetime)
            else None
        )

        return TechnicalAnalysis(
            symbol=summary["symbol"],
            current_price=summary.get("current_price"),
            ma_25=summary.get("ma_25"),
            divergence_rate=summary.get("divergence_rate"),
            dividend_yield=summary.get("dividend_yield"),
            volume_avg_20=summary.get("volume_avg_20"),
            ma_trend=summary.get("ma_trend"),
            price_trend=summary.get("price_trend"),
            last_updated=last_updated,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats/system", response_model=SystemStats)
async def get_system_stats(
    market_filter: str = Query(default="prime", description="市場区分フィルタ"),
):
    """システム統計情報を取得。

    Args:
        market_filter: 市場区分（prime, standard, growth）。空文字で全市場。
    """
    try:
        db_manager = DatabaseManager()
        # 空文字の場合はNoneに変換
        filter_value = market_filter if market_filter else None
        stats = db_manager.get_database_stats(market_filter=filter_value)

        return SystemStats(
            symbols_with_prices=stats.get("symbols_with_prices", 0),
            latest_price_date=stats.get("latest_price_date"),
            market_filter=stats.get("market_filter"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/run/{symbol}")
async def run_analysis(symbol: str):
    """個別銘柄の技術分析を実行"""
    try:
        analyzer = TechnicalAnalyzerService()

        # 分析実行
        result = analyzer.analyze_single_stock(symbol)

        if not result:
            raise HTTPException(status_code=400, detail="分析に失敗しました")

        return {"message": f"銘柄 {symbol} の分析が完了しました", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
