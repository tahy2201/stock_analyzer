import logging
from typing import Optional

from backend.services.analysis.technical_analyzer import TechnicalAnalysisService
from backend.services.data.stock_data_service import StockDataService
from backend.services.filtering.company_filter_service import CompanyFilterService
from backend.services.jpx.jpx_service import JPXService
from backend.shared.config.models import FilterCriteria
from backend.shared.config.settings import LOG_DATE_FORMAT, LOG_FORMAT
from backend.shared.database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


class BatchRunner:
    """バッチ処理の実行を管理するメインクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

        # サービスクラスの初期化
        self.jpx_service = JPXService(self.db_manager)
        self.company_filter_service = CompanyFilterService(self.db_manager)
        self.stock_data_service = StockDataService(self.db_manager)
        self.technical_analysis_service = TechnicalAnalysisService(self.db_manager)

    def exec(self, filter_criteria: FilterCriteria) -> None:
        """
        バッチ処理を実行
        """
        logger.info("バッチ処理開始")

        try:
            # JPXファイル取り込み
            self.run_jpx_update()

            # 企業フィルタ
            targets = self.run_company_filtering(filter_criteria)

            if not targets:
                logger.warning("フィルタリング対象が見つかりませんでした")
                return

            # 株価データ更新
            self.run_stock_data_update(targets)

            # 技術分析実行
            self.run_technical_analysis(targets)

            logger.info("バッチ処理完了")

        except Exception as e:
            logger.error(f"バッチ処理エラー: {e}")
            raise

    def run_jpx_update(self) -> bool:
        """
        JPXデータ更新を実行
        """
        logger.info("JPXデータ更新開始")

        try:
            success = self.jpx_service.update_jpx_data()

            if success:
                logger.info("JPXデータ更新完了")
            else:
                logger.warning("JPXデータ更新失敗")

            return success

        except Exception as e:
            logger.error(f"JPXデータ更新エラー: {e}")
            return False

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
            logger.error(f"企業フィルタリングエラー: {e}")
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
            return results

        except Exception as e:
            logger.error(f"株価データ更新エラー: {e}")
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

            return results

        except Exception as e:
            logger.error(f"技術分析エラー: {e}")
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
            logger.error(f"投資候補銘柄取得エラー: {e}")
            return []
