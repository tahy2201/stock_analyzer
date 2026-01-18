import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent  # stock_analyzerディレクトリ

MA_PERIOD = 25
DIVERGENCE_THRESHOLD = 5.0
DIVIDEND_YIELD_MIN = 3.0
DIVIDEND_YIELD_MAX = 5.0

MIN_EMPLOYEES = 1000
MIN_REVENUE = 10_000_000_000

DATA_DAYS = 252
BATCH_SIZE = 50

# 環境変数でDATABASE_PATHを上書き可能に（Docker対応）
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", PROJECT_ROOT / "data" / "stock_data.db"))
DATA_DIR = DATABASE_PATH.parent  # データベースと同じディレクトリ

JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/01.html"
JPX_FILE_NAME = "data_j.xls"

LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(asctime)s], [%(levelname)s], %(name)s -- %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

YFINANCE_REQUEST_DELAY = 0.1

MARKET_INDICES = {"NIKKEI": "^N225", "TOPIX": "^TPX", "JASDAQ": "^JASDAQ"}

# Anthropic API設定
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 2000

# AI分析設定
AI_ANALYSIS_TIMEOUT_SECONDS = 60
AI_ANALYSIS_DATA_DAYS = 90

DATA_DIR.mkdir(exist_ok=True)
