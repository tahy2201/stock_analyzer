import logging
import sys
import traceback
from pathlib import Path
from typing import Optional

import click
import click_log

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from services.analysis.technical_analyzer import TechnicalAnalyzer
from services.data.stock_data_service import StockDataService
from services.filtering.company_filter_service import CompanyFilterService
from shared.config.models import FilterCriteria
from shared.config.logging_config import get_click_logger
from shared.database.database_manager import DatabaseManager

class BatchRunner:
    """バッチ処理の実行を管理するメインクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

        # サービスクラスの初期化
        self.company_filter_service = CompanyFilterService(self.db_manager)
        self.stock_data_service = StockDataService(self.db_manager)
        self.technical_analysis_service = TechnicalAnalyzer()

    def exec(self, filter_criteria: FilterCriteria) -> None:
        """
        バッチ処理を実行
        """
        logger.info("バッチ処理開始")

        try:
            # 企業フィルタ
            targets = self.run_company_filtering(filter_criteria)

            if not targets:
                logger.warning("フィルタリング対象が見つかりませんでした。処理を終了します。")
                return

            # 株価データ更新
            stock_results = self.run_stock_data_update(targets)
            if not stock_results:
                logger.warning("株価データ更新対象がありませんでした。処理をスキップします。")

            # 技術分析実行
            analysis_results = self.run_technical_analysis(targets)
            if not analysis_results:
                logger.warning("技術分析対象がありませんでした。処理をスキップします。")

            logger.info("バッチ処理完了")

        except Exception as e:
            logger.error(f"バッチ処理エラー: {e}", exc_info=True)
            raise


    def run_company_filtering(self, filter_criteria: FilterCriteria) -> list[str]:
        """
        企業フィルタリングを実行
        """
        logger.info("企業フィルタリング開始")

        try:
            symbols = self.company_filter_service.filter_companies(filter_criteria)
            logger.info(f"フィルタリング完了: {len(symbols)} 銘柄")
            return symbols

        except Exception as e:
            logger.error(f"企業フィルタリングエラー: {e}", exc_info=True)
            return []

    def run_stock_data_update(self, symbols: list[str]) -> dict:
        """
        株価データ更新を実行
        """
        logger.info("株価データ更新開始")

        try:
            results = self.stock_data_service.update_stock_data(symbols)

            price_success = sum(1 for success in results["price_updates"].values() if success)
            ticker_success = sum(1 for success in results["ticker_updates"].values() if success)

            logger.info(f"株価データ更新完了: 価格 {price_success}件, ティッカー {ticker_success}件")

            # 全ての銘柄で失敗した場合のみエラー（更新対象なしは正常）
            if len(symbols) > 0 and price_success == 0 and ticker_success == 0:
                # 更新対象がなかった場合は正常終了
                if not results["price_updates"] and not results["ticker_updates"]:
                    logger.info("全ての銘柄で最新データが既に存在します")
                else:
                    logger.error("株価データ更新が全て失敗しました")
                    return {}

            return results

        except Exception as e:
            logger.error(f"株価データ更新エラー: {e}", exc_info=True)
            return {}

    def run_technical_analysis(self, symbols: list[str]) -> dict:
        """
        技術分析を実行
        """
        logger.info("技術分析開始")

        try:
            results = self.technical_analysis_service.analyze_batch_stocks(symbols)

            success_count = sum(1 for result in results.values() if result is not None)
            logger.info(f"技術分析完了: 成功 {success_count}/{len(symbols)}")

            # 全ての銘柄で失敗した場合のみエラー（一部成功は正常）
            if len(symbols) > 0 and success_count == 0:
                logger.error("技術分析が全て失敗しました")
                return {}

            return results

        except Exception as e:
            logger.error(f"技術分析エラー: {e}", exc_info=True)
            return {}

    def get_investment_candidates(
        self,
        divergence_threshold: float = -5.0,
        dividend_min: float = 2.0,
        dividend_max: float = 6.0,
    ) -> list[dict]:
        """
        投資候補銘柄を取得
        """
        logger.info("投資候補銘柄取得開始")

        try:
            candidates = self.technical_analysis_service.get_investment_candidates(
                divergence_threshold=divergence_threshold,
                dividend_min=dividend_min,
                dividend_max=dividend_max,
            )

            logger.info(f"投資候補銘柄取得完了: {len(candidates)} 銘柄")
            return candidates

        except Exception as e:
            logger.error(f"投資候補銘柄取得エラー: {e}", exc_info=True)
            return []


# グローバルloggerを作成（main関数とBatchRunnerで共有）
logger = get_click_logger(__name__)

@click.command()
@click_log.simple_verbosity_option(logger)
@click.option(
    "--markets",
    type=click.Choice(['prime', 'standard', 'growth', 'all']),
    help="対象市場を指定"
)
@click.option(
    "--symbols",
    multiple=True,
    help="銘柄コードを指定（複数可）"
)
def main(markets: str | None, symbols: tuple[str, ...]) -> None:
    """株価データ更新バッチ処理

    指定した市場または銘柄の株価データを更新します。

    例:
    \b
        # プライム市場の株価更新
        uv run python batch/stock_updater.py --markets prime

        # 特定銘柄の株価更新
        uv run python batch/stock_updater.py --symbols 7203 --symbols 6758
    """

    if not markets and not symbols:
        logger.error("--markets または --symbols のいずれかを指定してください")
        sys.exit(1)

    logger.info("株価データ更新バッチを開始します")

    try:
        batch_runner = BatchRunner()

        # FilterCriteriaを作成
        filter_criteria = None
        if symbols:
            symbol_list = list(symbols)
            logger.info(f"指定銘柄: {symbol_list}")
            filter_criteria = FilterCriteria(specific_symbols=symbol_list)
        elif markets:
            logger.info(f"対象市場: {markets}")
            filter_criteria = FilterCriteria(markets=[markets] if markets != 'all' else None)

        if filter_criteria:
            # バッチ処理を実行
            batch_runner.exec(filter_criteria)
        else:
            logger.error("FilterCriteriaの作成に失敗しました")
            sys.exit(1)

    except Exception as e:
        logger.error(f"株価データ更新バッチエラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()