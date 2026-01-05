from dataclasses import dataclass
from typing import Optional


@dataclass
class FilterCriteria:
    """銘柄フィルタリング条件を定義するクラス"""

    # 市場区分フィルタ
    markets: Optional[list[str]] = None
    exclude_markets: Optional[list[str]] = None

    # 企業規模フィルタ
    is_enterprise_only: bool = False

    # 特定銘柄コードリスト
    specific_symbols: Optional[list[str]] = None

    # 企業規模フィルタ
    market_cap_min: Optional[int] = None
    market_cap_max: Optional[int] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    min_revenue: Optional[int] = None
    max_revenue: Optional[int] = None

    # 業種フィルタ
    sectors: Optional[list[str]] = None
    excluded_sectors: Optional[list[str]] = None

    # 配当利回りフィルタ
    min_dividend_yield: Optional[float] = None
    max_dividend_yield: Optional[float] = None

    # テクニカル指標フィルタ
    min_divergence_rate: Optional[float] = None
    max_divergence_rate: Optional[float] = None
    divergence_min: Optional[float] = None
    dividend_yield_min: Optional[float] = None
    dividend_yield_max: Optional[float] = None
