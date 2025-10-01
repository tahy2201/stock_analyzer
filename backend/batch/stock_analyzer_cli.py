#!/usr/bin/env python3
"""
Stock Analyzer バッチ実行スクリプト
Usage: cd backend && uv run python batch/stock_analyzer_cli.py [command] [options]
"""

import argparse
import sys

# ruff: noqa: E402
from batch.stock_updater import BatchRunner
from shared.config.logging_config import get_service_logger

logger = get_service_logger(__name__)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Stock Analyzer バッチ処理")

    # サブコマンドの設定
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')

    # 株価更新コマンド
    update_parser = subparsers.add_parser('update', help='株価データ更新')
    update_parser.add_argument('--symbols', nargs='+', help='銘柄コード（例: 7203 6758）')
    update_parser.add_argument('--markets', choices=['prime', 'standard', 'growth', 'all'],
                              default='prime', help='対象市場')
    update_parser.add_argument('--limit', type=int, default=100, help='更新銘柄数の上限')

    # テクニカル分析コマンド
    analysis_parser = subparsers.add_parser('analysis', help='テクニカル分析実行')
    analysis_parser.add_argument('--symbols', nargs='+', help='銘柄コード（例: 7203 6758）')
    analysis_parser.add_argument('--markets', choices=['prime', 'standard', 'growth', 'all'],
                                default='prime', help='対象市場')

    # 投資候補取得コマンド
    candidates_parser = subparsers.add_parser('candidates', help='投資候補銘柄取得')
    candidates_parser.add_argument('--divergence-threshold', type=float, default=-5.0,
                                  help='乖離率の閾値')
    candidates_parser.add_argument('--dividend-min', type=float, default=2.0,
                                  help='配当利回り下限')
    candidates_parser.add_argument('--dividend-max', type=float, default=6.0,
                                  help='配当利回り上限')

    # JPXデータ更新コマンド
    subparsers.add_parser('jpx', help='JPXデータ更新')

    # 旧形式の引数も対応（後方互換性）
    parser.add_argument('--symbols', nargs='+', help='銘柄コード（旧形式対応）')
    parser.add_argument('--markets', choices=['prime', 'standard', 'growth', 'all'],
                       help='対象市場（旧形式対応）')

    args = parser.parse_args()

    try:
        batch_runner = BatchRunner()

        # コマンドがない場合は旧形式として処理
        if not args.command:
            if args.symbols or args.markets:
                logger.info("旧形式のコマンドライン引数を検出。株価更新を実行します。")
                symbols = args.symbols or []
                if args.markets:
                    # 市場指定の場合は企業一覧から取得
                    companies = batch_runner.db_manager.get_companies(
                        is_enterprise_only=True,
                        markets=[args.markets] if args.markets != 'all' else None
                    )
                    symbols = [company['symbol'] for company in companies[:100]]

                if symbols:
                    logger.info(f"株価データ更新開始: {len(symbols)}銘柄")
                    results = batch_runner.run_stock_data_update(symbols)
                    logger.info(f"株価データ更新完了: {results}")
                else:
                    logger.warning("更新対象の銘柄が指定されていません")
            else:
                parser.print_help()
                return

        # サブコマンド処理
        elif args.command == 'update':
            symbols = args.symbols or []
            if args.markets and not symbols:
                # 市場指定の場合は企業一覧から取得
                companies = batch_runner.db_manager.get_companies(
                    is_enterprise_only=True,
                    markets=[args.markets] if args.markets != 'all' else None
                )
                symbols = [company['symbol'] for company in companies[:args.limit]]

            if symbols:
                logger.info(f"株価データ更新開始: {len(symbols)}銘柄")
                results = batch_runner.run_stock_data_update(symbols)
                logger.info(f"株価データ更新完了: {results}")
            else:
                logger.warning("更新対象の銘柄が指定されていません")

        elif args.command == 'analysis':
            symbols = args.symbols or []
            if args.markets and not symbols:
                companies = batch_runner.db_manager.get_companies(
                    is_enterprise_only=True,
                    markets=[args.markets] if args.markets != 'all' else None
                )
                symbols = [company['symbol'] for company in companies]

            if symbols:
                logger.info(f"テクニカル分析開始: {len(symbols)}銘柄")
                results = batch_runner.run_technical_analysis(symbols)
                logger.info(f"テクニカル分析完了: {results}")
            else:
                logger.warning("分析対象の銘柄が指定されていません")

        elif args.command == 'candidates':
            logger.info("投資候補銘柄取得開始")
            candidates = batch_runner.get_investment_candidates(
                divergence_threshold=args.divergence_threshold,
                dividend_min=args.dividend_min,
                dividend_max=args.dividend_max
            )
            logger.info(f"投資候補銘柄: {len(candidates)}銘柄")
            for candidate in candidates[:10]:  # 上位10銘柄を表示
                print(f"銘柄: {candidate.get('symbol', 'N/A')} "
                      f"会社名: {candidate.get('name', 'N/A')} "
                      f"乖離率: {candidate.get('divergence_rate', 'N/A')}%")

        elif args.command == 'jpx':
            logger.info("JPXデータ更新開始")
            from batch.jpx_importer import JPXBatchRunner
            jpx_runner = JPXBatchRunner()
            jpx_runner.run()
            logger.info("JPXデータ更新完了")

    except Exception as e:
        logger.error(f"バッチ処理エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
