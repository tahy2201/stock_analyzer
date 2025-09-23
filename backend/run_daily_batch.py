#!/usr/bin/env python3
"""
株式分析システム 日次バッチ処理
株価データ更新と技術分析を実行する日次バッチ
"""
import argparse
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from backend.batch.batch_runner import BatchRunner
from backend.shared.config.models import FilterCriteria
from backend.shared.config.settings import LOG_DATE_FORMAT, LOG_FORMAT, LOG_LEVEL

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
    datefmt=LOG_DATE_FORMAT,
    handlers=[logging.FileHandler("batch_log.txt"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_param() -> FilterCriteria:
    """
    コマンドライン引数を解析してフィルタ条件を作成
    """
    parser = argparse.ArgumentParser(description="株式分析システム 日次バッチ処理")

    parser.add_argument(
        "--mode",
        choices=["full", "daily", "data-only", "analysis-only", "filter-only"],
        default="daily",
        help="実行モード",
    )
    parser.add_argument("--symbols", type=str, help="特定銘柄のみ処理（カンマ区切り）")
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
    print("🚀 株式分析システム 日次バッチ処理を開始します")

    try:
        # コマンドライン引数からフィルタを作成
        filter_criteria = parse_param()

        # 日次バッチ処理のBatchRunnerを使用
        batch_runner = BatchRunner()
        batch_runner.exec(filter_criteria)

        print("✅ 日次バッチ処理が正常に完了しました")

    except Exception as e:
        logger.error(f"❌ 日次バッチ処理エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
