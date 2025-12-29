import logging
from typing import Optional

from shared.config.models import FilterCriteria
from shared.config.settings import LOG_DATE_FORMAT, LOG_FORMAT
from shared.database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
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

            # 特定銘柄が指定されている場合は、それらのみを返す
            if filter_criteria.specific_symbols:
                logger.info(f"特定銘柄フィルタ適用: {filter_criteria.specific_symbols}")
                # 指定された銘柄がデータベースに存在するかチェック
                valid_symbols = []
                for symbol in filter_criteria.specific_symbols:
                    if self.get_company_info(symbol):
                        valid_symbols.append(symbol)
                    else:
                        logger.warning(f"銘柄 {symbol} はデータベースに存在しません")

                logger.info(f"特定銘柄フィルタリング完了: {len(valid_symbols)} 銘柄")
                return valid_symbols

            # 通常のフィルタリング処理
            # marketsが指定されている場合、最初のマーケットのみ適用（複数指定には未対応）
            market_filter = None
            if filter_criteria.markets and len(filter_criteria.markets) > 0:
                market_filter = filter_criteria.markets[0]
                logger.info(f"市場フィルタ適用: {market_filter}")

            companies = self.db_manager.get_filtered_companies(
                divergence_min=filter_criteria.divergence_min,
                dividend_yield_min=filter_criteria.dividend_yield_min,
                dividend_yield_max=filter_criteria.dividend_yield_max,
                is_enterprise_only=filter_criteria.is_enterprise_only,
                market_filter=market_filter
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
            return self.db_manager.get_company_by_symbol(symbol)

        except Exception as e:
            logger.error(f"企業情報取得エラー {symbol}: {e}")
            return None

    def get_all_companies(self, limit: Optional[int] = None) -> list[dict]:
        """
        全企業リストを取得
        """
        try:
            # 既存のDBメソッドを使用してすべての企業を取得
            companies = self.db_manager.get_filtered_companies(is_enterprise_only=False)

            # limit適用
            if limit:
                companies = companies[:limit]

            logger.info(f"企業リスト取得完了: {len(companies)} 件")
            return companies

        except Exception as e:
            logger.error(f"企業リスト取得エラー: {e}")
            return []
