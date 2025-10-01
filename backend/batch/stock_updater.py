import logging
import traceback
from typing import Optional

from services.analysis.technical_analyzer import TechnicalAnalyzer
from services.data.stock_data_service import StockDataService
from services.filtering.company_filter_service import CompanyFilterService
from shared.config.models import FilterCriteria
from shared.config.logging_config import get_service_logger
from shared.database.database_manager import DatabaseManager

logger = get_service_logger(__name__)


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

            # 全ての銘柄で失敗した場合のみエラー（一部成功は正常）
            if len(symbols) > 0 and price_success == 0 and ticker_success == 0:
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