import logging
from typing import Optional

from backend.shared.database.database_manager import DatabaseManager
from backend.shared.utils.jpx_parser import JPXParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JPXService:
    """JPXデータ処理を担当するサービスクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()
        self.jpx_parser = JPXParser()

    def update_jpx_data(self) -> bool:
        """
        JPXデータを更新
        """
        try:
            logger.info("JPXデータ更新開始")

            # JPXファイルの読み込み
            companies_data = self.jpx_parser.parse_jpx_excel()

            if not companies_data:
                logger.warning("JPXデータが空です")
                return False

            # データベースに保存
            success = self.db_manager.insert_companies(companies_data)

            if success:
                logger.info(f"JPXデータ更新完了: {len(companies_data)} 件")
            else:
                logger.error("JPXデータ保存失敗")

            return success

        except Exception as e:
            logger.error(f"JPXデータ更新エラー: {e}")
            return False

    def get_company_list(self, market_filter: Optional[str] = None) -> list[dict]:
        """
        企業リストを取得
        """
        try:
            companies = self.db_manager.get_filtered_companies(
                market_filter=market_filter
            )
            return companies

        except Exception as e:
            logger.error(f"企業リスト取得エラー: {e}")
            return []