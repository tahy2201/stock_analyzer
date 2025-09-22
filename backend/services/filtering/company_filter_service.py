import logging
from typing import Optional

from backend.shared.config.models import FilterCriteria
from backend.shared.database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompanyFilterService:
    """企業フィルタリングを担当するサービスクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

    def filter_companies(self, filter_criteria: FilterCriteria) -> list[str]:
        """
        フィルタ条件に基づいて企業を抽出
        """
        try:
            logger.info(f"企業フィルタリング開始: {filter_criteria}")

            # データベースからフィルタリング
            companies = self.db_manager.get_filtered_companies(
                market_cap_min=filter_criteria.market_cap_min,
                market_cap_max=filter_criteria.market_cap_max,
                is_enterprise_only=filter_criteria.is_enterprise_only,
                exclude_markets=filter_criteria.exclude_markets
            )

            symbols = [company["symbol"] for company in companies]
            logger.info(f"フィルタリング完了: {len(symbols)} 銘柄が抽出されました")

            return symbols

        except Exception as e:
            logger.error(f"企業フィルタリングエラー: {e}")
            return []

    def get_company_info(self, symbol: str) -> Optional[dict]:
        """
        企業の基本情報を取得
        """
        try:
            companies = self.db_manager.get_filtered_companies(symbol_filter=symbol)
            return companies[0] if companies else None

        except Exception as e:
            logger.error(f"企業情報取得エラー {symbol}: {e}")
            return None

    def get_all_companies(self, limit: Optional[int] = None) -> list[dict]:
        """
        全企業リストを取得
        """
        try:
            companies = self.db_manager.get_filtered_companies(limit=limit)
            logger.info(f"企業リスト取得完了: {len(companies)} 件")
            return companies

        except Exception as e:
            logger.error(f"企業リスト取得エラー: {e}")
            return []