import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from utils.jpx_parser import JPXParser
from batch.data_collector import StockDataCollector
from batch.technical_analyzer import TechnicalAnalyzer
from batch.company_filter import CompanyFilter
from utils.market_analyzer import MarketAnalyzer
from database.database_manager import DatabaseManager
from config.settings import LOG_LEVEL, LOG_FORMAT

# ログ設定
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler('batch_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BatchRunner:
    def __init__(self):
        self.jpx_parser = JPXParser()
        self.data_collector = StockDataCollector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.company_filter = CompanyFilter()
        self.market_analyzer = MarketAnalyzer()
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

    def run_company_filtering(self, stock_codes: List[str] = []) -> bool:
        """
        企業フィルタリング実行
        """
        logger.info("=== 企業フィルタリング開始 ===")
        try:
            results = self.company_filter.update_company_enterprise_status(stock_codes)
            success_count = sum(1 for r in results.values() if r['success'])
            logger.info(f"企業フィルタリング完了: 成功 {success_count}/{len(results)}")
            return success_count > 0
        except Exception as e:
            logger.error(f"企業フィルタリングエラー: {e}")
            return False
    
    def run_stock_data_collection(self, stock_codes: List[str] = [], enterprise_only: bool = True) -> bool:
        """
        株価データ収集
        """
        logger.info("=== 株価データ収集開始 ===")
        try:
            if stock_codes:
                results = self.data_collector.update_specific_stocks(stock_codes)
                success_count = sum(1 for success in results.values() if success)
                logger.info(f"指定銘柄データ収集完了: 成功 {success_count}/{len(stock_codes)}")
                return success_count > 0
            else:
                results = self.data_collector.update_all_stocks(enterprise_only=enterprise_only)
                success = results['success'] > 0
                logger.info(f"全銘柄データ収集完了: 成功 {results['success']}/{results['total']}")
                return success
        except Exception as e:
            logger.error(f"株価データ収集エラー: {e}")
            return False
    
    def run_technical_analysis(self, symbols: List[str] = []) -> bool:
        """
        技術分析実行
        """
        logger.info("=== 技術分析開始 ===")
        try:
            if symbols:
                results = self.technical_analyzer.analyze_batch_stocks(symbols)
                success_count = sum(1 for r in results.values() if r is not None)
            else:
                # 全企業の技術分析
                companies = self.db_manager.get_companies(is_enterprise_only=True)
                symbols_list = [company['symbol'] for company in companies]
                results = self.technical_analyzer.analyze_batch_stocks(symbols_list)
                success_count = sum(1 for r in results.values() if r is not None)
            
            logger.info(f"技術分析完了: 成功 {success_count}")
            return success_count > 0
        except Exception as e:
            logger.error(f"技術分析エラー: {e}")
            return False
    
    def run_market_analysis(self) -> bool:
        """
        市場分析実行
        """
        logger.info("=== 市場分析開始 ===")
        try:
            summary = self.market_analyzer.get_market_summary()
            overheated_analysis = self.market_analyzer.is_market_overheated()
            
            logger.info(f"市場センチメント: {summary.get('overall_sentiment')}")
            logger.info(f"投資タイミング: {summary.get('investment_timing')}")
            logger.info(f"市場過熱状況: {'過熱' if overheated_analysis.get('overall_overheated') else '正常'}")
            
            # 結果をログに記録
            for index_name, analysis in summary.get('indices_analysis', {}).items():
                logger.info(f"  {index_name}: {analysis.get('trend')} (価格: {analysis.get('current_price', 0):.2f})")
            
            logger.info("市場分析完了")
            return True
        except Exception as e:
            logger.error(f"市場分析エラー: {e}")
            return False
    
    def run_investment_screening(self) -> bool:
        """
        投資候補スクリーニング
        """
        logger.info("=== 投資候補スクリーニング開始 ===")
        try:
            candidates = self.technical_analyzer.get_investment_candidates()
            
            logger.info(f"投資候補銘柄: {len(candidates)} 銘柄")
            
            # 上位候補をログに出力
            for i, candidate in enumerate(candidates[:10]):
                logger.info(
                    f"  {i+1:2d}. {candidate['symbol']} ({candidate['name'][:20]}): "
                    f"乖離率 {candidate.get('divergence_rate', 0):+.1f}%, "
                    f"配当 {candidate.get('dividend_yield', 0):.1f}%, "
                    f"スコア {candidate.get('analysis_score', 0):.1f}"
                )
            
            logger.info("投資候補スクリーニング完了")
            return True
        except Exception as e:
            logger.error(f"投資候補スクリーニングエラー: {e}")
            return False
    
    def run_full_batch(self, skip_jpx: bool = False) -> Dict[str, bool]:
        """
        フルバッチ処理実行
        """
        logger.info("=== フルバッチ処理開始 ===")
        start_time = datetime.now()
        
        results = {}
        
        # 1. JPXデータ更新（スキップ可能）
        if not skip_jpx:
            results['jpx_update'] = self.run_jpx_update()
        else:
            results['jpx_update'] = True
            logger.info("JPXデータ更新をスキップしました")
        
        # 2. 企業フィルタリング（JPXデータが成功した場合のみ）
        if results['jpx_update']:
            results['company_filtering'] = self.run_company_filtering()
        else:
            results['company_filtering'] = False
            logger.warning("JPXデータ更新失敗のため企業フィルタリングをスキップ")
        
        # 3. 株価データ収集
        results['stock_data_collection'] = self.run_stock_data_collection()
        
        # 4. 技術分析
        if results['stock_data_collection']:
            results['technical_analysis'] = self.run_technical_analysis()
        else:
            results['technical_analysis'] = False
            logger.warning("株価データ収集失敗のため技術分析をスキップ")
        
        # 5. 市場分析
        results['market_analysis'] = self.run_market_analysis()
        
        # 6. 投資候補スクリーニング
        if results['technical_analysis']:
            results['investment_screening'] = self.run_investment_screening()
        else:
            results['investment_screening'] = False
            logger.warning("技術分析失敗のため投資候補スクリーニングをスキップ")
        
        # 処理時間の計算
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=== フルバッチ処理完了 ===")
        logger.info(f"処理時間: {duration}")
        logger.info("処理結果:")
        for process, success in results.items():
            status = "成功" if success else "失敗"
            logger.info(f"  {process}: {status}")
        
        return results
    
    def run_daily_update(self) -> Dict[str, bool]:
        """
        日次更新処理
        """
        logger.info("=== 日次更新処理開始 ===")
        start_time = datetime.now()
        
        results = {}
        
        # 1. 株価データの差分更新
        results['stock_data_collection'] = self.run_stock_data_collection(enterprise_only=True)
        
        # 2. 技術分析の更新
        if results['stock_data_collection']:
            results['technical_analysis'] = self.run_technical_analysis()
        else:
            results['technical_analysis'] = False
        
        # 3. 市場分析
        results['market_analysis'] = self.run_market_analysis()
        
        # 4. 投資候補の更新
        if results['technical_analysis']:
            results['investment_screening'] = self.run_investment_screening()
        else:
            results['investment_screening'] = False
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=== 日次更新処理完了 ===")
        logger.info(f"処理時間: {duration}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='株式分析システム バッチ処理')
    parser.add_argument('--mode', 
                       choices=['full', 'daily', 'jpx-only', 'data-only', 'analysis-only', 'filter-only'],
                       default='daily',
                       help='実行モード')
    parser.add_argument('--symbols', 
                       type=str,
                       help='特定銘柄のみ処理（カンマ区切り）')
    parser.add_argument('--skip-jpx',
                       action='store_true',
                       help='JPXデータ更新をスキップ')
    parser.add_argument('--enterprise-only',
                       action='store_true',
                       default=True,
                       help='エンタープライズ企業のみ処理')
    
    args = parser.parse_args()
    
    # バッチランナーの初期化
    batch_runner = BatchRunner()
    
    # シンボルリストの処理
    stock_codes = []
    if args.symbols:
        stock_codes = [s.strip() for s in args.symbols.split(',')]

    results = {}
    try:
        if args.mode == 'full':
            results = batch_runner.run_full_batch(skip_jpx=args.skip_jpx)
        elif args.mode == 'daily':
            results = batch_runner.run_daily_update()
        elif args.mode == 'jpx-only':
            results = {'jpx_update': batch_runner.run_jpx_update()}
        elif args.mode == 'data-only':
            results = {'stock_data_collection': batch_runner.run_stock_data_collection(stock_codes, args.enterprise_only)}
        elif args.mode == 'analysis-only':
            results = {'technical_analysis': batch_runner.run_technical_analysis(stock_codes)}
        elif args.mode == 'filter-only':
            results = {'company_filtering': batch_runner.run_company_filtering(stock_codes)}

        # 終了コード
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info("全ての処理が成功しました")
            sys.exit(0)
        elif success_count > 0:
            logger.warning(f"一部の処理が失敗しました ({success_count}/{total_count})")
            sys.exit(1)
        else:
            logger.error("全ての処理が失敗しました")
            sys.exit(2)
            
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
        sys.exit(130)
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()