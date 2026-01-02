import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.filtering.company_filter_service import CompanyFilterService

router = APIRouter()
logger = logging.getLogger(__name__)

# レスポンスモデル
class CompanyInfo(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    market_cap: Optional[float] = None
    is_enterprise: Optional[bool] = None

class InvestmentCandidate(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    latest_price: Optional[float] = None
    divergence_rate: Optional[float] = None
    dividend_yield: Optional[float] = None
    analysis_score: Optional[float] = None
    price_change_1d: Optional[float] = None

@router.get("/", response_model=list[CompanyInfo])
async def get_companies(
    limit: int = Query(100, description="取得件数の上限"),
    market: Optional[str] = Query(None, description="市場区分でフィルタ"),
    sector: Optional[str] = Query(None, description="業種でフィルタ"),
    is_enterprise: Optional[bool] = Query(None, description="大企業のみ"),
    search: Optional[str] = Query(None, description="銘柄コードまたは銘柄名で検索")
):
    """企業リストを取得（検索とフィルタリングをサポート）。"""
    try:
        company_service = CompanyFilterService()

        # 検索時はデータベースレベルで検索、通常時は全件取得
        if search:
            companies = company_service.search_companies(
                search=search,
                limit=limit,
                market=market,
                sector=sector,
                is_enterprise=is_enterprise,
            )
        else:
            # 通常のフィルタリング（全件取得してからPythonでフィルタ）
            companies = company_service.get_all_companies(limit=limit)

            # フィルタを適用
            if market:
                companies = [c for c in companies if c.get("market") == market]
            if sector:
                companies = [c for c in companies if c.get("sector") == sector]
            if is_enterprise is not None:
                companies = [c for c in companies if c.get("is_enterprise") == is_enterprise]

        # レスポンスモデルに変換
        result = [
            CompanyInfo(
                symbol=company["symbol"],
                name=company.get("name"),
                sector=company.get("sector"),
                market=company.get("market"),
                market_cap=company.get("market_cap"),
                is_enterprise=company.get("is_enterprise"),
            )
            for company in companies
        ]

        return result

    except HTTPException:
        # HTTPExceptionはそのまま再送出
        raise
    except ValueError as e:
        logger.error(f"Invalid value in get_companies: {e}")
        raise HTTPException(status_code=400, detail="不正な入力です") from None
    except Exception as e:
        logger.error(f"Unexpected error in get_companies: {e}")
        raise HTTPException(status_code=500, detail="サーバーエラーが発生しました") from None

@router.get("/{symbol}", response_model=CompanyInfo)
async def get_company(symbol: str):
    """個別企業の詳細情報を取得。"""
    try:
        company_service = CompanyFilterService()
        company = company_service.get_company_info(symbol)

        if not company:
            raise HTTPException(status_code=404, detail="企業が見つかりません")

        return CompanyInfo(
            symbol=company["symbol"],
            name=company.get("name"),
            sector=company.get("sector"),
            market=company.get("market"),
            market_cap=company.get("market_cap"),
            is_enterprise=company.get("is_enterprise"),
        )

    except HTTPException:
        # HTTPExceptionはそのまま再送出
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_company for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="サーバーエラーが発生しました") from None

@router.get("/candidates/investment", response_model=list[InvestmentCandidate])
async def get_investment_candidates(
    divergence_threshold: float = Query(-5.0, description="乖離率の閾値"),
    dividend_min: float = Query(2.0, description="配当利回りの最小値"),
    dividend_max: float = Query(6.0, description="配当利回りの最大値"),
    limit: int = Query(50, description="取得件数の上限"),
):
    """投資候補銘柄を取得。"""
    try:
        from services.analysis.technical_analyzer import TechnicalAnalyzer

        analyzer = TechnicalAnalyzer()
        candidates = analyzer.get_investment_candidates(
            divergence_threshold=divergence_threshold,
            dividend_min=dividend_min,
            dividend_max=dividend_max,
        )

        # 上限件数でカット
        candidates = candidates[:limit]

        # レスポンスモデルに変換
        result = [
            InvestmentCandidate(
                symbol=candidate["symbol"],
                name=candidate.get("name"),
                sector=candidate.get("sector"),
                market=candidate.get("market"),
                latest_price=candidate.get("latest_price"),
                divergence_rate=candidate.get("divergence_rate"),
                dividend_yield=candidate.get("dividend_yield"),
                analysis_score=candidate.get("analysis_score"),
                price_change_1d=candidate.get("price_change_1d"),
            )
            for candidate in candidates
        ]

        return result

    except HTTPException:
        # HTTPExceptionはそのまま再送出
        raise
    except ValueError as e:
        logger.error(f"Invalid value in get_investment_candidates: {e}")
        raise HTTPException(status_code=400, detail="不正な入力です") from None
    except Exception as e:
        logger.error(f"Unexpected error in get_investment_candidates: {e}")
        raise HTTPException(status_code=500, detail="サーバーエラーが発生しました") from None
