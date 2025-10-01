#!/usr/bin/env python3
"""
JPXファイル取り込み専用バッチ処理
JPXファイルは毎日更新されるものではないため、独立したバッチとして分離
"""
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from services.jpx.jpx_service import JPXService
from shared.config.logging_config import setup_jpx_logging
from shared.database.database_manager import DatabaseManager

# ログ設定（JPX専用のログファイルを使用）
logger = setup_jpx_logging()


class JPXBatchRunner:
    """JPXファイル取り込み専用のバッチランナー"""

    def __init__(self, db_manager: DatabaseManager = None) -> None:
        self.db_manager = db_manager or DatabaseManager()
        self.jpx_service = JPXService(self.db_manager)

    def run(self) -> bool:
        """
        JPXファイル取り込み処理を実行
        """
        logger.info("JPXファイル取り込みバッチ開始")

        try:
            success = self.jpx_service.update_jpx_data()

            if success:
                logger.info("JPXファイル取り込み完了")
                print("✅ JPXファイル取り込みが正常に完了しました")
            else:
                logger.error("JPXファイル取り込み失敗")
                print("❌ JPXファイル取り込みに失敗しました")

            return success

        except Exception as e:
            logger.error(f"JPXファイル取り込みエラー: {e}", exc_info=True)
            print(f"❌ JPXファイル取り込みエラー: {e}")
            return False


def main() -> None:
    print("🚀 JPXファイル取り込みバッチを開始します")

    try:
        jpx_batch_runner = JPXBatchRunner()
        success = jpx_batch_runner.run()

        if not success:
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ JPXバッチ処理エラー: {e}", exc_info=True)
        print(f"❌ JPXバッチ処理エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()