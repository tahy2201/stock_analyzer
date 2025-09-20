import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf

from config.settings import DATA_DAYS, MARKET_INDICES, YFINANCE_REQUEST_DELAY
from database.database_manager import DatabaseManager
from utils.jpx_parser import JPXParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeoutSession(requests.Session):
    """requests.Session subclass that enforces a default timeout."""

    def __init__(self, timeout: float) -> None:
        super().__init__()
        self._timeout = timeout

    def request(self, *args, **kwargs):  # type: ignore[override]
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._timeout
        return super().request(*args, **kwargs)


class StockDataCollector:
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()
        self.jpx_parser = JPXParser()
        self.error_log_dir = "logs/errors"
        os.makedirs(self.error_log_dir, exist_ok=True)

    def format_symbol(self, symbol: str) -> str:
        """
        日本株のシンボルをyfinance形式に変換
        例: 7203 → 7203.T
        """
        if not symbol.endswith(".T"):
            return f"{symbol}.T"
        return symbol

    def collect_market_indices(self) -> dict[str, bool]:
        """
        市場指数データの収集
        """
        results = {}

        for index_name, symbol in MARKET_INDICES.items():
            try:
                logger.info(f"市場指数データ収集: {index_name} ({symbol})")

                ticker = yf.Ticker(symbol)
                hist: pd.DataFrame = ticker.history(period=f"{DATA_DAYS}d")

                if not hist.empty:
                    # 列名を小文字に統一
                    hist.columns = pd.Index([col.lower() for col in hist.columns], dtype=str)

                    # データベース保存（市場指数は特別なシンボルとして保存）
                    success = self.db_manager.insert_stock_prices(f"INDEX_{index_name}", hist)
                    results[index_name] = success

                    if success:
                        logger.info(f"市場指数データ保存完了: {index_name}")
                    else:
                        logger.error(f"市場指数データ保存失敗: {index_name}")
                else:
                    logger.warning(f"市場指数データが取得できませんでした: {index_name}")
                    results[index_name] = False

                time.sleep(YFINANCE_REQUEST_DELAY)

            except Exception as e:
                logger.error(f"市場指数データ収集エラー {index_name}: {e}")
                results[index_name] = False

        return results


    def update_tiker(self, symbols: list[str]) -> dict[str, int]:
        """
        ティッカー情報の更新（価格とinfo両方）
        戻り値: {'prices_success': int, 'info_success': int, 'total': int}
        """
        logger.info(f"ティッカー情報更新開始: {len(symbols)} 銘柄")

        # 1. 価格データの更新
        prices_success = self.update_tiker_prices(symbols)

        # 2. 企業情報の更新
        info_success = self.update_tiker_info(symbols)

        prices_count = sum(1 for success in prices_success.values() if success)
        info_count = sum(1 for success in info_success.values() if success)
        total_count = len(symbols)

        logger.info(f"ティッカー情報更新完了: 価格成功 {prices_count}/{total_count}, 情報成功 {info_count}/{total_count}")

        return {
            'prices_success': prices_count,
            'info_success': info_count,
            'total': total_count
        }

    def update_tiker_prices(self, symbols: list[str]) -> dict[str, bool]:
        """
        ティッカー価格データの効率的な更新（1000件ずつ処理）
        """
        logger.info(f"価格データ更新開始: {len(symbols)} 銘柄")
        results = {}

        try:
            # 各銘柄の最新日付を取得
            latest_dates = self.db_manager.get_latest_price_dates(symbols)

            # データが存在しない銘柄は過去252日分、存在する銘柄は最新日から取得
            start_date = datetime.now() - timedelta(days=DATA_DAYS + 30)
            if latest_dates and any(date for date in latest_dates.values() if date):
                # 最新データがある場合は、最古の日付から取得
                oldest_date = min(date for date in latest_dates.values() if date)
                if oldest_date > start_date:
                    start_date = oldest_date

            # 1000件ずつバッチ処理
            batch_size = 1000
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                logger.info(f"価格データ取得バッチ {i//batch_size + 1}: {len(batch_symbols)} 銘柄")

                try:
                    # 一括でデータ取得
                    prices_data = self.get_stock_prices(batch_symbols, start_date, datetime.now())

                    if prices_data.empty:
                        logger.warning(f"バッチ {i//batch_size + 1}: データ取得できませんでした")
                        for symbol in batch_symbols:
                            results[symbol] = False
                        continue

                    # 銘柄ごとにデータベースに保存
                    for symbol in batch_symbols:
                        try:
                            formatted_symbol = self.format_symbol(symbol)

                            # マルチインデックスの場合の処理
                            if isinstance(prices_data.columns, pd.MultiIndex):
                                # yf.downloadの結果は(列名, フォーマット済みシンボル)の形式
                                symbol_data = prices_data.xs(formatted_symbol, level=1, axis=1)
                            else:
                                # 単一銘柄の場合
                                symbol_data = prices_data

                            if not symbol_data.empty:
                                # 列名を小文字に統一（型チェック対応）
                                if isinstance(symbol_data, pd.DataFrame):
                                    symbol_data.columns = pd.Index([col.lower() for col in symbol_data.columns], dtype=str)
                                else:
                                    # Seriesの場合はDataFrameに変換
                                    symbol_data = symbol_data.to_frame().T
                                    symbol_data.columns = pd.Index([col.lower() for col in symbol_data.columns], dtype=str)

                                # 必要な列のみ抽出
                                required_columns = ["open", "high", "low", "close", "volume"]
                                if all(col in symbol_data.columns for col in required_columns):
                                    symbol_data = symbol_data[required_columns].dropna()

                                    if not symbol_data.empty:
                                        # DB保存時は元のシンボル（フォーマット前）を使用
                                        success = self.db_manager.insert_stock_prices(symbol, symbol_data)
                                        results[symbol] = success
                                        if success:
                                            logger.debug(f"価格データ保存成功: {symbol} ({len(symbol_data)} 日分)")
                                        else:
                                            logger.warning(f"価格データ保存失敗: {symbol}")
                                    else:
                                        results[symbol] = False
                                        logger.warning(f"データが空（欠損除去後）: {symbol}")
                                else:
                                    missing_cols = [col for col in required_columns if col not in symbol_data.columns]
                                    results[symbol] = False
                                    logger.warning(f"必要な列が不足 {symbol}: {missing_cols}")
                            else:
                                results[symbol] = False
                                logger.warning(f"銘柄データが空: {symbol}")

                        except Exception as e:
                            logger.error(f"銘柄処理エラー {symbol}: {e}")
                            results[symbol] = False

                    # バッチ間の待機（API制限対策）
                    if i + batch_size < len(symbols):
                        logger.info("次のバッチまで待機中...")
                        time.sleep(2)

                except Exception as e:
                    logger.error(f"バッチ {i//batch_size + 1} 処理エラー: {e}")
                    for symbol in batch_symbols:
                        results[symbol] = False

            success_count = sum(1 for success in results.values() if success)
            logger.info(f"価格データ更新完了: 成功 {success_count}/{len(symbols)}")

        except Exception as e:
            logger.error(f"価格データ更新エラー: {e}")
            results = dict.fromkeys(symbols, False)

        return results

    def update_tiker_info(self, symbols: list[str]) -> dict[str, bool]:
        """
        ティッカー企業情報の更新（100件ずつ処理、レート制限考慮）
        """
        logger.info(f"企業情報更新開始: {len(symbols)} 銘柄")
        results = {}

        try:
            # 100件ずつバッチ処理（レート制限対策）
            batch_size = 100
            max_attempts = 3
            retry_delay = 2
            timeout_seconds = 10.0
            abort_processing = False
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                logger.info(f"企業情報取得バッチ {i//batch_size + 1}: {len(batch_symbols)} 銘柄")

                try:
                    info_data = {}
                    for attempt in range(1, max_attempts + 1):
                        # yfinance Tickersで一括取得
                        info_data = self.get_stock_info(batch_symbols, timeout_seconds)
                        if info_data:
                            break

                        logger.warning(
                            "企業情報取得失敗 (試行 %d/%d): %s",
                            attempt,
                            max_attempts,
                            ",".join(batch_symbols)
                        )

                        if attempt < max_attempts:
                            logger.info("再試行前に待機中 (%d秒)...", retry_delay)
                            time.sleep(retry_delay)

                    if not info_data:
                        logger.error(
                            "企業情報バッチ %d: 3回試行後も取得できませんでした。処理を終了します",
                            i // batch_size + 1
                        )
                        for symbol in batch_symbols:
                            results[symbol] = False

                        for remaining_symbol in symbols[i + batch_size:]:
                            if remaining_symbol not in results:
                                results[remaining_symbol] = False

                        abort_processing = True
                        break

                    if abort_processing:
                        break

                    if not info_data:
                        logger.warning(f"バッチ {i//batch_size + 1}: 企業情報が取得できませんでした")
                        for symbol in batch_symbols:
                            results[symbol] = False
                        continue

                    # 銘柄ごとに処理
                    for symbol in batch_symbols:
                        try:
                            formatted_symbol = self.format_symbol(symbol)

                            if formatted_symbol in info_data:
                                ticker_info = info_data[formatted_symbol]

                                # 基本的なデータの存在チェック
                                if ticker_info and isinstance(ticker_info, dict) and len(ticker_info) > 5:
                                    # データベースに保存（元のシンボルを使用）
                                    success = self.db_manager.insert_ticker_info(symbol, ticker_info)
                                    results[symbol] = success

                                    if success:
                                        logger.debug(f"企業情報保存成功: {symbol}")
                                    else:
                                        logger.warning(f"企業情報保存失敗: {symbol}")
                                else:
                                    results[symbol] = False
                                    logger.warning(f"企業情報が空または不正: {symbol}")
                            else:
                                results[symbol] = False
                                logger.warning(f"企業情報が見つかりません: {symbol}")

                        except Exception as e:
                            logger.error(f"企業情報処理エラー {symbol}: {e}")
                            results[symbol] = False

                    # バッチ間の待機（API制限対策 - infoは特に厳しい）
                    if i + batch_size < len(symbols):
                        logger.info("次のバッチまで待機中（企業情報取得はレート制限あり）...")
                        time.sleep(10)  # 10秒待機

                except Exception as e:
                    logger.error(f"企業情報バッチ {i//batch_size + 1} 処理エラー: {e}")
                    for symbol in batch_symbols:
                        results[symbol] = False

                if abort_processing:
                    break

            success_count = sum(1 for success in results.values() if success)
            logger.info(f"企業情報更新完了: 成功 {success_count}/{len(symbols)}")

        except Exception as e:
            logger.error(f"企業情報更新エラー: {e}")
            results = dict.fromkeys(symbols, False)

        return results

    def get_stock_prices(self, symbols: list[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        formatted_symbols = [self.format_symbol(symbol) for symbol in symbols]

        prices = None
        try:
            # Yahoo Financeから株価データを取得
            prices = yf.download(
                formatted_symbols,
                auto_adjust=True,
                start=start_date,
                end=end_date
            )
        except Exception as e:
            logger.error(f"Error fetching data for {formatted_symbols}: {e}")
        return prices if prices is not None else pd.DataFrame()

    def get_stock_info(self, symbols: list[str], timeout: float = 10.0) -> dict[str, dict]:
        formatted_symbols = [self.format_symbol(symbol) for symbol in symbols]

        info = None
        try:
            # Yahoo Financeから株価データを取得
            session = TimeoutSession(timeout)
            tickers = yf.Tickers(" ".join(formatted_symbols), session=session)
            info = {symbol: tickers.tickers[symbol].info for symbol in formatted_symbols}
        except Exception as e:
            logger.error(f"Error fetching data for {formatted_symbols}: {e}")
        return info if info is not None else {}


if __name__ == "__main__":
    collector = StockDataCollector()

    # テスト用: 特定銘柄のデータ収集
    test_symbols = ["7203", "6758", "9984"]  # トヨタ、ソニーG、ソフトバンクG

    print("テスト用データ収集を開始...")
    results = collector.update_tiker_info(test_symbols)

    print("結果:")
    for symbol, success in results.items():
        status = "成功" if success else "失敗"
        print(f"  {symbol}: {status}")

    # データベースの統計情報
    stats = collector.db_manager.get_database_stats()
    print("\nデータベース統計:")
    print(f"  企業数: {stats.get('companies_count', 0)}")
    print(f"  株価データ有り: {stats.get('symbols_with_prices', 0)}")
    print(f"  最新価格日付: {stats.get('latest_price_date', 'N/A')}")
