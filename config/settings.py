import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MA_PERIOD = 25
DIVERGENCE_THRESHOLD = 5.0
DIVIDEND_YIELD_MIN = 3.0
DIVIDEND_YIELD_MAX = 5.0

MIN_EMPLOYEES = 1000
MIN_REVENUE = 10_000_000_000

DATA_DAYS = 252
BATCH_SIZE = 50

DATABASE_PATH = BASE_DIR / "database" / "stock_data.db"
DATA_DIR = BASE_DIR / "data"

JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/01.html"
JPX_FILE_NAME = "data_j.xls"

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

YFINANCE_REQUEST_DELAY = 0.1

MARKET_INDICES = {
    "NIKKEI": "^N225",
    "TOPIX": "^TPX",
    "JASDAQ": "^JASDAQ"
}

DATA_DIR.mkdir(exist_ok=True)