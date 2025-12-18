#!/usr/bin/env python3
"""
JPXファイル取り込み専用バッチ処理
JPXファイルは毎日更新されるものではないため、独立したバッチとして分離
"""
import sys
from pathlib import Path
from typing import Optional

import click
import click_log

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from services.jpx.jpx_service import JPXService
from shared.config.logging_config import get_click_logger
from shared.database.database_manager import DatabaseManager

# ログ設定（click_log用）
logger = get_click_logger(__name__)


class JPXBatchRunner:
    """JPXファイル取り込み専用のバッチランナー"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
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
                logger.info("JPXファイル取り込みが正常に完了しました")
            else:
                logger.error("JPXファイル取り込みに失敗しました")

            return success

        except Exception as e:
            logger.error(f"JPXファイル取り込みエラー: {e}", exc_info=True)
            return False


@click.command()
@click_log.simple_verbosity_option(logger)
def main() -> None:
    """JPXファイル取り込みバッチ処理

    JPX（日本取引所グループ）の上場企業一覧Excelファイルを
    データベースに取り込みます。
    """
    logger.info("JPXファイル取り込みバッチを開始します")

    try:
        jpx_batch_runner = JPXBatchRunner()
        success = jpx_batch_runner.run()

        if not success:
            sys.exit(1)

    except Exception as e:
        logger.error(f"JPXバッチ処理エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
