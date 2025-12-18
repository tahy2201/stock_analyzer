import hashlib
import logging
import time
from typing import Optional

import pandas as pd
import yfinance as yf

from shared.config.settings import YFINANCE_REQUEST_DELAY
from shared.database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataService:
    """株価データ収集を担当するサービスクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

    def get_ticker_info_update_interval_days(self, symbol: str, base_days: int = 14) -> int:
        """
        銘柄のハッシュ値に基づいて更新間隔を分散
        """
        hash_obj = hashlib.md5(symbol.encode('utf-8'))
        offset = int(hash_obj.hexdigest(), 16) % 7
        return base_days + offset

    def collect_stock_prices(self, symbols: list[str]) -> dict[str, bool]:
        """
        株価データを収集
        """
        results = {}

        logger.info(f"株価データ収集開始: {len(symbols)} 銘柄")

        for i, symbol in enumerate(symbols):
            if (i + 1) % 50 == 0:
                logger.info(f"進捗: {i + 1}/{len(symbols)}")

            try:
                # レート制限の適用
                time.sleep(YFINANCE_REQUEST_DELAY)

                # 日本株式のティッカー形式に変換
                yf_ticker = f"{symbol}.T"

                # 過去1年分のデータを取得
                ticker = yf.Ticker(yf_ticker)
                hist = ticker.history(period="1y")

                if hist.empty:
                    logger.warning(f"株価データが空です: {symbol}")
                    results[symbol] = False
                    continue

                # データベース形式に変換
                price_data = pd.DataFrame({
                    'date': hist.index.date,
                    'open': hist['Open'],
                    'high': hist['High'],
                    'low': hist['Low'],
                    'close': hist['Close'],
                    'volume': hist['Volume']
                })

                # データベースに保存
                success = self.db_manager.insert_stock_prices(symbol, price_data)
                results[symbol] = success

                if success:
                    logger.debug(f"株価データ保存完了: {symbol}")
                else:
                    logger.error(f"株価データ保存失敗: {symbol}")

            except Exception as e:
                logger.error(f"株価データ収集エラー {symbol}: {e}")
                results[symbol] = False

        success_count = sum(1 for success in results.values() if success)
        logger.info(f"株価データ収集完了: 成功 {success_count}/{len(symbols)}")

        return results

    def collect_ticker_info(self, symbols: list[str]) -> dict[str, bool]:
        """
        ティッカー情報を収集
        """
        results = {}

        logger.info(f"ティッカー情報収集開始: {len(symbols)} 銘柄")

        for i, symbol in enumerate(symbols):
            if (i + 1) % 50 == 0:
                logger.info(f"進捗: {i + 1}/{len(symbols)}")

            try:
                # レート制限の適用
                time.sleep(YFINANCE_REQUEST_DELAY)

                # 日本株式のティッカー形式に変換
                yf_ticker = f"{symbol}.T"

                ticker = yf.Ticker(yf_ticker)
                info = ticker.info

                if not info:
                    logger.warning(f"ティッカー情報が空です: {symbol}")
                    results[symbol] = False
                    continue

                # データベースに保存
                success = self.db_manager.insert_ticker_info(symbol, info)
                results[symbol] = success

                if success:
                    logger.debug(f"ティッカー情報保存完了: {symbol}")
                else:
                    logger.error(f"ティッカー情報保存失敗: {symbol}")

            except Exception as e:
                logger.error(f"ティッカー情報収集エラー {symbol}: {e}")
                results[symbol] = False

        success_count = sum(1 for success in results.values() if success)
        logger.info(f"ティッカー情報収集完了: 成功 {success_count}/{len(symbols)}")

        return results

    def update_stock_data(self, symbols: list[str]) -> dict[str, object]:
        """
        株価データとティッカー情報の差分更新
        """
        import datetime

        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        # 価格データの更新対象を特定
        price_symbols_to_update = []
        ticker_symbols_to_update = []

        for symbol in symbols:
            # 価格データの更新判定
            latest_price_data = self.db_manager.get_latest_stock_price_date(symbol)
            if latest_price_data is None:
                price_symbols_to_update.append(symbol)
            elif latest_price_data.date() < yesterday:
                price_symbols_to_update.append(symbol)

            # ティッカー情報の更新判定（分散間隔）
            interval_days = self.get_ticker_info_update_interval_days(symbol)
            threshold_date = datetime.date.today() - datetime.timedelta(days=interval_days)

            latest_ticker_date = self.db_manager.get_latest_ticker_info_date(symbol)
            if latest_ticker_date is None:
                ticker_symbols_to_update.append(symbol)
            elif latest_ticker_date.date() < threshold_date:
                ticker_symbols_to_update.append(symbol)

        logger.info(f"更新対象: 価格データ {len(price_symbols_to_update)} 銘柄, ティッカー情報 {len(ticker_symbols_to_update)} 銘柄")

        # データ収集実行
        price_results = {}
        ticker_results = {}

        if price_symbols_to_update:
            price_results = self.collect_stock_prices(price_symbols_to_update)

        if ticker_symbols_to_update:
            ticker_results = self.collect_ticker_info(ticker_symbols_to_update)

        return {
            "price_updates": price_results,
            "ticker_updates": ticker_results,
            "price_symbols_checked": len(symbols),
            "ticker_symbols_checked": len(symbols),
            "price_symbols_updated": len(price_symbols_to_update),
            "ticker_symbols_updated": len(ticker_symbols_to_update)
        }
