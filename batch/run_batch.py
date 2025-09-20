import argparse
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from batch.company_filter import CompanyFilter
from batch.data_collector import StockDataCollector
from batch.technical_analyzer import TechnicalAnalyzer
from config.settings import LOG_FORMAT, LOG_LEVEL
from database.database_manager import DatabaseManager
from utils.jpx_parser import JPXParser
from utils.market_analyzer import MarketAnalyzer
from utils.symbol_filter import FilterCriteria, SymbolFilter

# 市場コードマッピング
MARKET_CODE_MAPPING = {
    "prime": "プライム（内国株式）",
    "standard": "スタンダード（内国株式）",
    "growth": "グロース（内国株式）",
}

# ログ設定
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[logging.FileHandler("batch_log.txt"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class BatchRunner:
    def __init__(self) -> None:
        self.jpx_parser = JPXParser()
        self.data_collector = StockDataCollector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.company_filter = CompanyFilter()
        self.market_analyzer = MarketAnalyzer()
        self.symbol_filter = SymbolFilter()
        self.db_manager = DatabaseManager()

    def run_jpx_update(self) -> bool:
        """
        JPXデータの更新
        """
        logger.info("=== JPXデータ更新開始 ===")
        try:
            success = self.jpx_parser.update_jpx_data()
            if success:
                logger.info("JPXデータ更新完了")
            else:
                logger.error("JPXデータ更新失敗")
            return success
        except Exception as e:
            logger.error(f"JPXデータ更新エラー: {e}")
            return False

    def run_company_filtering(self, filter_criteria: FilterCriteria) -> list[str]:
        """
        企業フィルタリング実行
        """
        logger.info("=== 企業フィルタリング開始 ===")

        results: list[str] = []
        if filter_criteria.specific_symbols:
            results = filter_criteria.specific_symbols
        else:
            results = self.symbol_filter.get_filtered_symbols(filter_criteria)
        return results

    def run_stock_data_collection(self, symbols: list[str]) -> bool:
        """
        株価データ収集
        """
        logger.info("=== 株価データ収集開始 ===")
        try:
            logger.info(f"対象銘柄数: {len(symbols)}")
            results = self.data_collector.update_tiker(symbols)

            prices_success = results['prices_success']
            info_success = results['info_success']
            total = results['total']

            logger.info(f"株価データ収集完了: 価格 {prices_success}/{total}, 企業情報 {info_success}/{total}")
            return prices_success > 0 or info_success > 0
        except Exception as e:
            logger.error(f"株価データ収集エラー: {e}")
            return False

    def run_technical_analysis(self, symbols: list[str]) -> bool:
        """
        技術分析実行
        """
        logger.info("=== 技術分析開始 ===")
        try:
            results = self.technical_analyzer.analyze_batch_stocks(symbols)
            success_count = sum(1 for r in results.values() if r is not None)
            logger.info(f"技術分析完了: 成功 {success_count}")
            return success_count > 0
        except Exception as e:
            logger.error(f"技術分析エラー: {e}")
            return False

    # def run_market_analysis(self) -> bool:
    #     """
    #     市場分析実行
    #     """
    #     logger.info("=== 市場分析開始 ===")
    #     try:
    #         summary = self.market_analyzer.get_market_summary()
    #         overheated_analysis = self.market_analyzer.is_market_overheated()

    #         logger.info(f"市場センチメント: {summary.get('overall_sentiment')}")
    #         logger.info(f"投資タイミング: {summary.get('investment_timing')}")
    #         logger.info(f"市場過熱状況: {'過熱' if overheated_analysis.get('overall_overheated') else '正常'}")

    #         # 結果をログに記録
    #         for index_name, analysis in summary.get('indices_analysis', {}).items():
    #             logger.info(f"  {index_name}: {analysis.get('trend')} (価格: {analysis.get('current_price', 0):.2f})")

    #         logger.info("市場分析完了")
    #         return True
    #     except Exception as e:
    #         logger.error(f"市場分析エラー: {e}")
    #         return False

    # def run_daily_update(self, filter_criteria: Optional[FilterCriteria] = None) -> Dict[str, bool]:
    #     """
    #     日次更新処理
    #     """
    #     logger.info("=== 日次更新処理開始 ===")
    #     start_time = datetime.now()

    #     # デフォルトフィルタ（エンタープライズ企業のみ）
    #     if filter_criteria is None:
    #         filter_criteria = FilterCriteria(is_enterprise_only=True)

    #     logger.info(f"フィルタ条件: {self.symbol_filter.get_filter_summary(filter_criteria)}")

    #     results = {}

    #     # 1. 株価データの差分更新
    #     results['stock_data_collection'] = self.run_stock_data_collection(filter_criteria)

    #     # 2. 技術分析の更新
    #     if results['stock_data_collection']:
    #         results['technical_analysis'] = self.run_technical_analysis(filter_criteria)
    #     else:
    #         results['technical_analysis'] = False

    #     # 3. 市場分析
    #     results['market_analysis'] = self.run_market_analysis()

    #     # 4. 投資候補の更新
    #     if results['technical_analysis']:
    #         results['investment_screening'] = self.run_investment_screening()
    #     else:
    #         results['investment_screening'] = False

    #     end_time = datetime.now()
    #     duration = end_time - start_time

    #     logger.info("=== 日次更新処理完了 ===")
    #     logger.info(f"処理時間: {duration}")

    #     return results

    def exec(self, filter_criteria: FilterCriteria) -> None:
        # jpxファイル取り込み
        self.run_jpx_update()

        # 企業フィルタ
        targets = self.run_company_filtering(filter_criteria)

        # 株価データ取得
        self.run_stock_data_collection(targets)

        # 株価データ分析
        # self.run_technical_analysis(targets)

def parse_param() -> FilterCriteria:
    """
    コマンドライン引数を解析してフィルタ条件を作成
    """
    parser = argparse.ArgumentParser(description="株式分析システム バッチ処理")
    # 実行モード
    # 実装済み: primeのみ、スタンダードのみ、グロースのみ、全市場
    # 未実装: エンタープライズ企業のみ、従業員数1000人以上、時価総額1000億以上、配当利回り3%以上
    parser.add_argument(
        "--mode",
        choices=["full", "daily", "jpx-only", "data-only", "analysis-only", "filter-only"],
        default="daily",
        help="実行モード",
    )
    parser.add_argument("--symbols", type=str, help="特定銘柄のみ処理（カンマ区切り）")
    parser.add_argument("--skip-jpx", action="store_true", help="JPXデータ更新をスキップ")
    parser.add_argument(
        "--enterprise-only", action="store_true", default=True, help="エンタープライズ企業のみ処理"
    )
    parser.add_argument(
        "--markets", type=str, help="処理対象市場（カンマ区切り）例: prime,standard,growth"
    )

    args = parser.parse_args()
    filter_criteria = FilterCriteria()

    # 市場リストの処理（英語コードを日本語名に変換）
    if args.markets:
        market_codes = [m.strip() for m in args.markets.split(',')]
        markets = [MARKET_CODE_MAPPING.get(code, code) for code in market_codes]
        # Noneを除外
        filter_criteria.markets = [m for m in markets if m is not None]
        logger.info(f"指定市場: {filter_criteria.markets}")

    # エンタープライズフィルタ
    if args.enterprise_only:
        filter_criteria.is_enterprise_only = True

    # 特定銘柄
    if args.symbols:
        filter_criteria.specific_symbols = [s.strip() for s in args.symbols.split(',')]

    return filter_criteria

def main() -> None:
    print("バッチ処理を開始します")

    # コマンドライン引数からフィルタを作成
    filter_criteria = parse_param()

    batch_runner = BatchRunner()
    batch_runner.exec(filter_criteria)

if __name__ == "__main__":
    main()
