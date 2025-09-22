from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.analysis.technical_analyzer import TechnicalAnalysisService
from backend.shared.database.database_manager import DatabaseManager

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
    companies_count: int
    symbols_with_prices: int
    symbols_with_technical: int
    latest_price_date: Optional[str] = None
    latest_analysis_date: Optional[str] = None

@router.get("/{symbol}", response_model=TechnicalAnalysis)
async def get_technical_analysis(symbol: str):
    """個別銘柄の技術分析を取得"""
    try:
        analyzer = TechnicalAnalysisService()

        # 技術分析サマリーを取得
        summary = analyzer.get_technical_summary(symbol)

        if not summary:
            raise HTTPException(status_code=404, detail="技術分析データが見つかりません")

        return TechnicalAnalysis(
            symbol=summary["symbol"],
            current_price=summary.get("current_price"),
            ma_25=summary.get("ma_25"),
            divergence_rate=summary.get("divergence_rate"),
            dividend_yield=summary.get("dividend_yield"),
            volume_avg_20=summary.get("volume_avg_20"),
            ma_trend=summary.get("ma_trend"),
            price_trend=summary.get("price_trend"),
            last_updated=summary.get("last_updated").strftime("%Y-%m-%d") if summary.get("last_updated") else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/system", response_model=SystemStats)
async def get_system_stats():
    """システム統計情報を取得"""
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_database_stats()

        return SystemStats(
            companies_count=stats.get("companies_count", 0),
            symbols_with_prices=stats.get("symbols_with_prices", 0),
            symbols_with_technical=stats.get("symbols_with_technical", 0),
            latest_price_date=stats.get("latest_price_date"),
            latest_analysis_date=stats.get("latest_analysis_date")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run/{symbol}")
async def run_analysis(symbol: str):
    """個別銘柄の技術分析を実行"""
    try:
        analyzer = TechnicalAnalysisService()

        # 分析実行
        result = analyzer.analyze_single_stock(symbol)

        if not result:
            raise HTTPException(status_code=400, detail="分析に失敗しました")

        return {
            "message": f"銘柄 {symbol} の分析が完了しました",
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
