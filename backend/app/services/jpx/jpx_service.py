from typing import Optional

from app.config.logging_config import get_service_logger
from app.database.database_manager import DatabaseManager
from app.services.jpx.jpx_file_parse_service import JPXFileParseService

logger = get_service_logger(__name__)


class JPXService:
    """JPXデータ処理を担当するサービスクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()
        self.jpx_parser = JPXFileParseService()

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
