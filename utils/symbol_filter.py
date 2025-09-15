import logging
from dataclasses import dataclass
from typing import Optional

from database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """銘柄フィルタリング条件を定義するクラス"""

    # 市場区分フィルタ
    markets: Optional[list[str]] = None

    # 企業規模フィルタ
    is_enterprise_only: bool = False

    # 今後追加予定のフィルタ
    min_market_cap: Optional[int] = None
    max_market_cap: Optional[int] = None
    sectors: Optional[list[str]] = None
    excluded_sectors: Optional[list[str]] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    min_revenue: Optional[int] = None
    max_revenue: Optional[int] = None

    # 配当利回りフィルタ
    min_dividend_yield: Optional[float] = None
    max_dividend_yield: Optional[float] = None

    # テクニカル指標フィルタ
    min_divergence_rate: Optional[float] = None
    max_divergence_rate: Optional[float] = None

    """
    引数からFilterCriteriaオブジェクトを作成

    使用例:
    filter_criteria = symbol_filter.create_filter_from_args(
        markets=['プライム（内国株式）'],
        is_enterprise_only=True,
        min_employees=1000
    )
        """


class SymbolFilter:
    """銘柄フィルタリングを担当するクラス"""

    def __init__(self) -> None:
        self.db_manager = DatabaseManager()

    def get_filtered_symbols(self, criteria: FilterCriteria) -> list[str]:
        """
        フィルタ条件に基づいて銘柄リストを取得

        Args:
            criteria: フィルタリング条件

        Returns:
            条件に合致する銘柄コードのリスト
        """
        companies = self._get_companies_by_criteria(criteria)
        symbols = [company["symbol"] for company in companies if company.get("symbol")]

        logger.info(f"フィルタリング結果: {len(symbols)} 銘柄が条件に合致")
        return symbols

    def get_filtered_companies(self, criteria: FilterCriteria) -> list[dict]:
        """
        フィルタ条件に基づいて企業情報を取得

        Args:
            criteria: フィルタリング条件

        Returns:
            条件に合致する企業情報のリスト
        """
        try:
            return self._get_companies_by_criteria(criteria)
        except Exception as e:
            logger.error(f"企業情報フィルタリングエラー: {e}")
            return []

    def _get_companies_by_criteria(self, criteria: FilterCriteria) -> list[dict]:
        """
        内部メソッド: フィルタ条件に基づいて企業データを取得
        """
        # 基本的なフィルタリング（既存のget_companies使用）
        companies = self.db_manager.get_companies(
            is_enterprise_only=criteria.is_enterprise_only, markets=criteria.markets
        )

        # 追加フィルタリング
        filtered_companies = []
        for company in companies:
            if self._matches_criteria(company, criteria):
                filtered_companies.append(company)

        return filtered_companies

    def _matches_criteria(self, company: dict, criteria: FilterCriteria) -> bool:
        """
        企業が条件に合致するかチェック
        """
        # 従業員数フィルタ
        employees = company.get("employees")
        if criteria.min_employees is not None and (
            employees is None or employees < criteria.min_employees
        ):
            return False
        if criteria.max_employees is not None and (
            employees is not None and employees > criteria.max_employees
        ):
            return False

        # 売上高フィルタ
        revenue = company.get("revenue")
        if criteria.min_revenue is not None and (revenue is None or revenue < criteria.min_revenue):
            return False
        if criteria.max_revenue is not None and (
            revenue is not None and revenue > criteria.max_revenue
        ):
            return False

        # 業種フィルタ
        sector = company.get("sector", "").lower()
        if criteria.sectors:
            if not any(s.lower() in sector for s in criteria.sectors):
                return False

        if criteria.excluded_sectors:
            if any(s.lower() in sector for s in criteria.excluded_sectors):
                return False

        # 配当利回りフィルタ
        dividend_yield = company.get("dividend_yield")
        if criteria.min_dividend_yield is not None and (
            dividend_yield is None or dividend_yield < criteria.min_dividend_yield
        ):
            return False
        if criteria.max_dividend_yield is not None and (
            dividend_yield is not None and dividend_yield > criteria.max_dividend_yield
        ):
            return False

        return True

    def get_predefined_filter(self, filter_name: str) -> FilterCriteria:
        """
        よく使用されるフィルタ条件の定義済みセットを取得
        """
        predefined_filters = {
            "prime_enterprise": FilterCriteria(
                markets=["プライム（内国株式）"], is_enterprise_only=True
            ),
            "all_enterprise": FilterCriteria(is_enterprise_only=True),
            "prime_all": FilterCriteria(markets=["プライム（内国株式）"]),
            "large_cap": FilterCriteria(
                is_enterprise_only=True,
                min_employees=1000,
                min_revenue=10_000_000_000,  # 100億円
            ),
            "high_dividend": FilterCriteria(is_enterprise_only=True, min_dividend_yield=3.0),
            "tech_companies": FilterCriteria(
                is_enterprise_only=True, sectors=["情報・通信業", "Technology", "Software"]
            ),
        }

        if filter_name not in predefined_filters:
            logger.warning(f"未定義のフィルタ名: {filter_name}")
            return FilterCriteria()

        return predefined_filters[filter_name]

    def get_filter_summary(self, criteria: FilterCriteria) -> str:
        """
        フィルタ条件の概要を文字列で取得（ログ用）
        """
        conditions = []

        if criteria.markets:
            conditions.append(f"市場: {', '.join(criteria.markets)}")

        if criteria.is_enterprise_only:
            conditions.append("エンタープライズ企業のみ")

        if criteria.min_employees:
            conditions.append(f"従業員数 >= {criteria.min_employees:,}")

        if criteria.min_revenue:
            conditions.append(f"売上高 >= {criteria.min_revenue:,}")

        if criteria.sectors:
            conditions.append(f"業種: {', '.join(criteria.sectors)}")

        if criteria.excluded_sectors:
            conditions.append(f"除外業種: {', '.join(criteria.excluded_sectors)}")

        if criteria.min_dividend_yield:
            conditions.append(f"配当利回り >= {criteria.min_dividend_yield}%")

        return "; ".join(conditions) if conditions else "フィルタなし"


if __name__ == "__main__":
    # テスト用
    symbol_filter = SymbolFilter()

    # プライム市場のエンタープライズ企業を取得
    criteria = symbol_filter.get_predefined_filter("prime_enterprise")
    symbols = symbol_filter.get_filtered_symbols(criteria)

    print(f"プライム市場エンタープライズ企業: {len(symbols)} 銘柄")
    print(f"フィルタ条件: {symbol_filter.get_filter_summary(criteria)}")
    print(f"最初の10銘柄: {symbols[:10]}")
