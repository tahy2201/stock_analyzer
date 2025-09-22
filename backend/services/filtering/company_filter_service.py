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
            companies = self.db_manager.get_filtered_companies(
                divergence_min=filter_criteria.divergence_min,
                dividend_yield_min=filter_criteria.dividend_yield_min,
                dividend_yield_max=filter_criteria.dividend_yield_max,
                is_enterprise_only=filter_criteria.is_enterprise_only
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
            # 既存のDBメソッドを使用（symbol_filterパラメータは未対応のため、別途実装が必要）
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM companies WHERE symbol = ?", (symbol,))
                result = cursor.fetchone()
                return dict(result) if result else None

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