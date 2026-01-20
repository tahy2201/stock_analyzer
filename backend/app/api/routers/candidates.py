import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.analysis.technical_analyzer_service import TechnicalAnalyzerService
from app.utils.numeric import safe_float

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


@router.get("/", response_model=list[InvestmentCandidate])
async def get_investment_candidates(
    limit: int = 50,
    max_divergence: float = -5.0,  # 株価が移動平均線より5%以上低い（乖離率-5.0%以下）
    min_dividend: float = 0.0,  # 配当利回り最小値（0.0で実質無効化）
    max_dividend: float = 100.0,  # 配当利回り最大値（100.0で実質無効化）
    market_filter: str = "prime",  # prime企業のみ
    min_score: Optional[float] = None,  # 最小スコア
):
    """投資候補銘柄を取得。

    Args:
        limit: 取得上限
        max_divergence: 乖離率上限（マイナス値、例: -5.0で5%以上下落の銘柄）
        min_dividend: 配当利回り最小値
        max_dividend: 配当利回り最大値
        market_filter: 市場区分（prime, standard, growth）
        min_score: 分析スコア最小値（0〜10、指定時はこの値以上の銘柄のみ）
    """
    try:
        analyzer = TechnicalAnalyzerService()
        # 空文字の場合はNoneに変換
        filter_value = market_filter if market_filter else None

        # 投資候補を取得
        candidates = analyzer.get_investment_candidates(
            divergence_threshold=max_divergence,  # 乖離率の上限（マイナス値）
            dividend_min=min_dividend,
            dividend_max=max_dividend,
            market_filter=filter_value,
        )

        # スコアフィルタを適用（analysis_scoreがNoneの銘柄は除外）
        if min_score is not None:
            candidates = [
                c for c in candidates
                if c.get("analysis_score") is not None and c["analysis_score"] >= min_score
            ]

        # レスポンス形式に変換（NaN値を除外）
        result = []
        for candidate in candidates[:limit]:
            result.append(
                InvestmentCandidate(
                    symbol=candidate.get("symbol") or "",
                    name=candidate.get("name"),
                    sector=candidate.get("sector"),
                    market=candidate.get("market"),
                    current_price=safe_float(candidate.get("current_price")),
                    ma_25=safe_float(candidate.get("ma_25")),
                    divergence_rate=safe_float(candidate.get("divergence_rate")),
                    dividend_yield=safe_float(candidate.get("dividend_yield")),
                    analysis_score=safe_float(candidate.get("analysis_score")),
                    latest_price=safe_float(candidate.get("latest_price")),
                    price_change_1d=safe_float(candidate.get("price_change_1d")),
                )
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/count")
async def get_candidates_count(
    market_filter: str = "prime",
    max_divergence: float = -5.0,
    min_dividend: float = 3.0,
):
    """投資候補銘柄数を取得。

    ダッシュボードのデフォルト条件（乖離率-5%以下、配当利回り3%以上）でカウント。

    Args:
        market_filter: 市場区分（prime, standard, growth）。デフォルトはprime。
        max_divergence: 乖離率上限。デフォルトは-5.0。
        min_dividend: 配当利回り最小値。デフォルトは3.0。
    """
    try:
        analyzer = TechnicalAnalyzerService()
        # 空文字の場合はNoneに変換してフィルタ無効化
        filter_value = market_filter if market_filter else None
        candidates = analyzer.get_investment_candidates(
            divergence_threshold=max_divergence,
            dividend_min=min_dividend,
            market_filter=filter_value,
        )

        return {
            "total_candidates": len(candidates),
            "high_score": len([c for c in candidates if c.get("analysis_score", 0) >= 5]),
            "medium_score": len([c for c in candidates if 3 <= c.get("analysis_score", 0) < 5]),
            "low_score": len([c for c in candidates if c.get("analysis_score", 0) < 3]),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
