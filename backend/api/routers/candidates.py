import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from batch.technical_analyzer import TechnicalAnalyzer

router = APIRouter()

# レスポンスモデル
class InvestmentCandidate(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    current_price: Optional[float] = None
    ma_25: Optional[float] = None
    divergence_rate: Optional[float] = None
    dividend_yield: Optional[float] = None
    analysis_score: Optional[float] = None
    latest_price: Optional[float] = None
    price_change_1d: Optional[float] = None

@router.get("/", response_model=List[InvestmentCandidate])
async def get_investment_candidates(
    limit: int = 50,
    min_divergence: float = -10.0,
    min_dividend: float = 1.0,
    max_dividend: float = 10.0
):
    """投資候補銘柄を取得"""
    try:
        analyzer = TechnicalAnalyzer()

        # 投資候補を取得
        candidates = analyzer.get_investment_candidates(
            divergence_threshold=min_divergence,
            dividend_min=min_dividend,
            dividend_max=max_dividend
        )

        # レスポンス形式に変換
        result = []
        for candidate in candidates[:limit]:
            result.append(InvestmentCandidate(
                symbol=candidate.get("symbol"),
                name=candidate.get("name"),
                sector=candidate.get("sector"),
                market=candidate.get("market"),
                current_price=candidate.get("current_price"),
                ma_25=candidate.get("ma_25"),
                divergence_rate=candidate.get("divergence_rate"),
                dividend_yield=candidate.get("dividend_yield"),
                analysis_score=candidate.get("analysis_score"),
                latest_price=candidate.get("latest_price"),
                price_change_1d=candidate.get("price_change_1d")
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count")
async def get_candidates_count():
    """投資候補銘柄数を取得"""
    try:
        analyzer = TechnicalAnalyzer()
        candidates = analyzer.get_investment_candidates()

        return {
            "total_candidates": len(candidates),
            "high_score": len([c for c in candidates if c.get("analysis_score", 0) >= 5]),
            "medium_score": len([c for c in candidates if 3 <= c.get("analysis_score", 0) < 5]),
            "low_score": len([c for c in candidates if c.get("analysis_score", 0) < 3])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
