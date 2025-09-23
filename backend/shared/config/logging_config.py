import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .settings import LOG_DATE_FORMAT, LOG_FORMAT, LOG_LEVEL


def setup_api_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    API用のログ設定
    週1でローテーション、8週間で削除
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"

    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / "api.log"

    logger = logging.getLogger("api")
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 既存のハンドラーをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ローテーションハンドラー（週1回、8週間保持）
    rotating_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when='W0',  # 毎週月曜日
        interval=1,
        backupCount=8,  # 8週間分保持
        encoding='utf-8'
    )
    rotating_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    logger.addHandler(rotating_handler)
    logger.addHandler(console_handler)

    # 親ロガーに伝搬しないように設定
    logger.propagate = False

    return logger


def setup_batch_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Batch用のログ設定
    週1でローテーション、8週間で削除
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"

    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / "batch.log"

    logger = logging.getLogger("batch")
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 既存のハンドラーをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ローテーションハンドラー（週1回、8週間保持）
    rotating_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when='W0',  # 毎週月曜日
        interval=1,
        backupCount=8,  # 8週間分保持
        encoding='utf-8'
    )
    rotating_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    logger.addHandler(rotating_handler)
    logger.addHandler(console_handler)

    # 親ロガーに伝搬しないように設定
    logger.propagate = False

    return logger


def setup_jpx_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    JPX専用のログ設定
    週1でローテーション、8週間で削除
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"

    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / "jpx.log"

    logger = logging.getLogger("jpx")
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 既存のハンドラーをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ローテーションハンドラー（週1回、8週間保持）
    rotating_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when='W0',  # 毎週月曜日
        interval=1,
        backupCount=8,  # 8週間分保持
        encoding='utf-8'
    )
    rotating_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    logger.addHandler(rotating_handler)
    logger.addHandler(console_handler)

    # 親ロガーに伝搬しないように設定
    logger.propagate = False

    return logger


def get_service_logger(service_name: str, log_dir: Optional[Path] = None) -> logging.Logger:
    """
    各サービス用の共通ログ設定
    APIまたはBatchのどちらかのログ設定を継承
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 親ロガーからハンドラーを継承
    if not logger.handlers:
        formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger