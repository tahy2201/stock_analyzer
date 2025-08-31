import yfinance as yf
import pandas as pd
import time
import logging
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from config.settings import (
    DATA_DAYS, BATCH_SIZE, YFINANCE_REQUEST_DELAY,
    MARKET_INDICES
)
from database.database_manager import DatabaseManager
from utils.jpx_parser import JPXParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataCollector:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.jpx_parser = JPXParser()
        self.error_log_dir = "logs/errors"
        os.makedirs(self.error_log_dir, exist_ok=True)
        
    def format_symbol(self, symbol: str) -> str:
        """
        日本株のシンボルをyfinance形式に変換
        例: 7203 → 7203.T
        """
        if not symbol.endswith('.T'):
            return f"{symbol}.T"
        return symbol
    
    def log_error_to_file(self, symbol: str, error_info: Dict):
        """
        エラー情報をファイルに出力
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = os.path.join(self.error_log_dir, f"{symbol}_{timestamp}.json")
            
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"エラーログ保存: {error_file}")
            
        except Exception as e:
            logger.error(f"エラーログ保存失敗 {symbol}: {e}")
    
    def fetch_stock_data_with_retry(self, symbol: str, period_days: int = DATA_DAYS, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """
        リトライ機能付きの株価データ取得
        """
        formatted_symbol = self.format_symbol(symbol)
        error_info = {
            'symbol': symbol,
            'formatted_symbol': formatted_symbol,
            'attempts': [],
            'final_result': None,
            'timestamp': datetime.now()
        }
        
        for attempt in range(max_retries + 1):
            attempt_info = {
                'attempt_number': attempt + 1,
                'timestamp': datetime.now(),
                'error': None,
                'success': False
            }
            
            try:
                logger.info(f"株価データ取得試行 {attempt + 1}/{max_retries + 1}: {symbol}")
                
                # yfinanceでデータ取得
                ticker = yf.Ticker(formatted_symbol)
                
                # 期間を指定してデータ取得
                end_date = datetime.now()
                start_date = end_date - timedelta(days=period_days + 30)
                
                hist = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval='1d',
                    auto_adjust=True,
                    prepost=False
                )
                
                if hist.empty:
                    error_msg = f"yfinanceからデータが返されませんでした"
                    attempt_info['error'] = error_msg
                    logger.warning(f"{symbol}: {error_msg}")
                    
                    if attempt == max_retries:
                        error_info['final_result'] = 'no_data'
                        self.log_error_to_file(symbol, error_info)
                        return None
                    
                    # 次の試行まで待機
                    wait_time = (attempt + 1) * 5
                    logger.info(f"データなし、{wait_time}秒待機後リトライ")
                    time.sleep(wait_time)
                    continue
                
                # 列名を小文字に統一
                hist.columns = [col.lower() for col in hist.columns]
                
                # 必要な列のみ抽出
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                if not all(col in hist.columns for col in required_columns):
                    missing_cols = [col for col in required_columns if col not in hist.columns]
                    error_msg = f"必要な列が不足: {missing_cols}"
                    attempt_info['error'] = error_msg
                    logger.warning(f"{symbol}: {error_msg}")
                    
                    if attempt == max_retries:
                        error_info['final_result'] = 'missing_columns'
                        self.log_error_to_file(symbol, error_info)
                        return None
                    
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue
                
                hist = hist[required_columns]
                
                # 欠損データの処理
                hist = hist.dropna()
                
                if hist.empty:
                    error_msg = "欠損データ除去後にデータが空になりました"
                    attempt_info['error'] = error_msg
                    logger.warning(f"{symbol}: {error_msg}")
                    
                    if attempt == max_retries:
                        error_info['final_result'] = 'empty_after_cleanup'
                        self.log_error_to_file(symbol, error_info)
                        return None
                    
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue
                
                # 指定期間分のデータのみ保持
                if len(hist) > period_days:
                    hist = hist.tail(period_days)
                
                attempt_info['success'] = True
                attempt_info['data_points'] = len(hist)
                error_info['attempts'].append(attempt_info)
                error_info['final_result'] = 'success'
                
                logger.info(f"{symbol}: {len(hist)} 日分のデータを取得成功")
                
                # API制限対策の待機
                time.sleep(YFINANCE_REQUEST_DELAY)
                
                return hist
                
            except Exception as e:
                error_msg = str(e)
                attempt_info['error'] = error_msg
                error_info['attempts'].append(attempt_info)
                
                logger.error(f"株価データ取得エラー {symbol} (試行 {attempt + 1}): {error_msg}")
                
                # 最後の試行でもエラーの場合
                if attempt == max_retries:
                    error_info['final_result'] = 'max_retries_exceeded'
                    self.log_error_to_file(symbol, error_info)
                    logger.error(f"最大リトライ回数に達しました。全体処理を中断します: {symbol}")
                    raise Exception(f"株価データ取得に失敗 (最大{max_retries + 1}回試行): {symbol} - レート制限により処理を中断")
                
                # 次の試行まで待機（指数バックオフ）
                wait_time = (2 ** attempt) * 5  # 5, 10, 20秒
                logger.info(f"エラー発生、{wait_time}秒待機後リトライ")
                time.sleep(wait_time)
                
        return None
    
    def fetch_stock_data(self, symbol: str, period_days: int = DATA_DAYS) -> Optional[pd.DataFrame]:
        """
        単一銘柄の株価データを取得（下位互換のため）
        """
        return self.fetch_stock_data_with_retry(symbol, period_days)
    
    def fetch_dividend_info(self, symbol: str) -> Optional[float]:
        """
        配当利回り情報を取得
        """
        formatted_symbol = self.format_symbol(symbol)
        
        try:
            ticker = yf.Ticker(formatted_symbol)
            info = ticker.info
            
            # 配当利回りの取得（複数のキーを試行）
            dividend_yield = None
            for key in ['dividendYield', 'trailingAnnualDividendYield', 'forwardAnnualDividendYield']:
                if key in info and info[key] is not None:
                    dividend_yield = float(info[key]) * 100  # パーセンテージに変換
                    break
            
            if dividend_yield is None:
                # 配当履歴から計算を試行
                dividends = ticker.dividends
                if not dividends.empty and len(dividends) > 0:
                    # 直近1年の配当合計
                    one_year_ago = datetime.now() - timedelta(days=365)
                    recent_dividends = dividends[dividends.index >= one_year_ago]
                    
                    if not recent_dividends.empty:
                        annual_dividend = recent_dividends.sum()
                        
                        # 現在の株価
                        current_price = ticker.history(period='1d')['Close'].iloc[-1]
                        
                        if current_price > 0:
                            dividend_yield = (annual_dividend / current_price) * 100
            
            return dividend_yield
            
        except Exception as e:
            logger.warning(f"配当情報取得エラー {symbol}: {e}")
            return None
    
    def save_dividend_to_company(self, symbol: str, dividend_yield: float) -> bool:
        """
        配当利回りをcompaniesテーブルに保存
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE companies SET dividend_yield = ? WHERE symbol = ?
                ''', (dividend_yield, symbol))
                conn.commit()
                logger.debug(f"配当利回り保存: {symbol} = {dividend_yield}%")
                return True
        except Exception as e:
            logger.error(f"配当利回り保存エラー {symbol}: {e}")
            return False
    
    def get_last_trading_day(self, from_date: datetime | None = None) -> datetime:
        """
        最後の取引日を取得（土日祝日を除く）
        """
        if from_date is None:
            from_date = datetime.now()
        
        # 日本の祝日（主要なもの）
        japanese_holidays_2025 = [
            datetime(2025, 1, 1),   # 元日
            datetime(2025, 1, 13),  # 成人の日
            datetime(2025, 2, 11),  # 建国記念の日
            datetime(2025, 2, 23),  # 天皇誕生日
            datetime(2025, 3, 20),  # 春分の日
            datetime(2025, 4, 29),  # 昭和の日
            datetime(2025, 5, 3),   # 憲法記念日
            datetime(2025, 5, 4),   # みどりの日
            datetime(2025, 5, 5),   # こどもの日
            datetime(2025, 7, 21),  # 海の日
            datetime(2025, 8, 11),  # 山の日
            datetime(2025, 9, 15),  # 敬老の日
            datetime(2025, 9, 23),  # 秋分の日
            datetime(2025, 10, 13), # スポーツの日
            datetime(2025, 11, 3),  # 文化の日
            datetime(2025, 11, 23), # 勤労感謝の日
            datetime(2025, 12, 31), # 年末（市場休業）
        ]
        
        # 年末年始の特別休業日
        year_end_holidays = []
        current_year = from_date.year
        for day in range(29, 32):  # 12/29-12/31
            try:
                year_end_holidays.append(datetime(current_year, 12, day))
            except ValueError:
                pass
        for day in range(1, 4):    # 1/1-1/3
            year_end_holidays.append(datetime(current_year + 1, 1, day))
        
        all_holidays = japanese_holidays_2025 + year_end_holidays
        
        # 現在日付から遡って最後の取引日を探す
        check_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for _ in range(10):  # 最大10日遡る
            # 平日かつ祝日でない場合は取引日
            if (check_date.weekday() < 5 and  # 月-金（0-4）
                not any(holiday.date() == check_date.date() for holiday in all_holidays)):
                return check_date
            
            check_date -= timedelta(days=1)
        
        # 見つからない場合は現在日付を返す
        return from_date

    def is_data_up_to_date(self, symbol: str, max_days_old: int = 1) -> bool:
        """
        株価データが最新かどうかをチェック（土日祝日を考慮）
        """
        try:
            existing_data = self.db_manager.get_stock_prices(symbol)
            if existing_data.empty:
                return False
            
            # 最新データの日付を取得
            latest_date = pd.to_datetime(existing_data.index[-1])
            
            # 最後の取引日を取得
            last_trading_day = self.get_last_trading_day()
            
            # 最新データが最後の取引日以降かチェック
            is_recent = latest_date.date() >= last_trading_day.date()
            
            if is_recent:
                logger.debug(f"{symbol}: 最新データ有り ({latest_date.date()}, 最終取引日: {last_trading_day.date()})")
            else:
                days_behind = (last_trading_day.date() - latest_date.date()).days
                logger.debug(f"{symbol}: データ更新が必要 ({latest_date.date()}, {days_behind}取引日遅れ)")
            
            return is_recent
            
        except Exception as e:
            logger.debug(f"{symbol}: データ確認エラー - {e}")
            return False

    def collect_single_stock(self, symbol: str, include_dividend: bool = True, force_update: bool = False) -> bool:
        """
        単一銘柄のデータ収集とデータベース保存
        """
        try:
            # 強制更新でない場合、最新データをチェック
            if not force_update and self.is_data_up_to_date(symbol):
                logger.info(f"データ収集スキップ (最新): {symbol}")
                return True
            
            logger.info(f"データ収集開始: {symbol}")
            
            # 株価データの取得
            price_data = self.fetch_stock_data(symbol)
            if price_data is None or price_data.empty:
                logger.warning(f"株価データが取得できませんでした: {symbol}")
                return False
            
            # データベースに株価データを保存
            success = self.db_manager.insert_stock_prices(symbol, price_data)
            if not success:
                logger.error(f"株価データ保存に失敗: {symbol}")
                return False
            
            # 配当情報の取得・保存（オプション）
            if include_dividend:
                dividend_yield = self.fetch_dividend_info(symbol)
                # 配当情報をcompaniesテーブルに保存
                if dividend_yield is not None:
                    self.save_dividend_to_company(symbol, dividend_yield)
            
            logger.info(f"データ収集完了: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"データ収集エラー {symbol}: {e}")
            return False
    
    def collect_batch_stocks(self, symbols: List[str], max_workers: int = 5) -> Dict[str, bool]:
        """
        複数銘柄のデータを並列収集
        """
        results = {}
        
        # バッチサイズで分割処理
        for i in range(0, len(symbols), BATCH_SIZE):
            batch_symbols = symbols[i:i + BATCH_SIZE]
            logger.info(f"バッチ処理中: {i+1}-{min(i+BATCH_SIZE, len(symbols))} / {len(symbols)}")
            
            # 並列処理でデータ収集
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 非同期タスクの送信
                future_to_symbol = {
                    executor.submit(self.collect_single_stock, symbol): symbol 
                    for symbol in batch_symbols
                }
                
                # 結果の収集
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        success = future.result(timeout=60)  # 60秒でタイムアウト
                        results[symbol] = success
                    except Exception as e:
                        logger.error(f"並列処理エラー {symbol}: {e}")
                        results[symbol] = False
            
            # バッチ間の待機（API制限対策）
            if i + BATCH_SIZE < len(symbols):
                logger.info(f"次のバッチまで待機中...")
                time.sleep(5)
        
        return results
    
    def collect_market_indices(self) -> Dict[str, bool]:
        """
        市場指数データの収集
        """
        results = {}
        
        for index_name, symbol in MARKET_INDICES.items():
            try:
                logger.info(f"市場指数データ収集: {index_name} ({symbol})")
                
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{DATA_DAYS}d")
                
                if not hist.empty:
                    # 列名を小文字に統一
                    hist.columns = [col.lower() for col in hist.columns]
                    
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
    
    def update_all_stocks(self, enterprise_only: bool = True, force_update: bool = False) -> Dict[str, int]:
        """
        全銘柄のデータ更新
        """
        logger.info("全銘柄データ更新を開始します")
        
        # 銘柄リストの取得
        companies = self.db_manager.get_companies(is_enterprise_only=enterprise_only)
        if not companies:
            logger.warning("銘柄データが見つかりません。先にJPXデータを更新してください。")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        symbols = [company['symbol'] for company in companies]
        logger.info(f"更新対象銘柄数: {len(symbols)}")
        
        # 最新データチェック（強制更新でない場合）
        if not force_update:
            up_to_date_count = 0
            symbols_to_update = []
            
            logger.info("既存データの確認中...")
            for symbol in symbols:
                if self.is_data_up_to_date(symbol):
                    up_to_date_count += 1
                else:
                    symbols_to_update.append(symbol)
            
            logger.info(f"最新データ有り: {up_to_date_count}銘柄, 更新必要: {len(symbols_to_update)}銘柄")
            symbols = symbols_to_update
        
        # 市場指数の更新
        logger.info("市場指数データの更新...")
        market_results = self.collect_market_indices()
        
        # 個別銘柄の更新
        if symbols:
            logger.info(f"個別銘柄データの更新... ({len(symbols)}銘柄)")
            stock_results = self.collect_batch_stocks(symbols)
        else:
            logger.info("更新が必要な銘柄がありません")
            stock_results = {}
        
        # 結果の集計
        success_count = sum(1 for success in stock_results.values() if success)
        failed_count = len(stock_results) - success_count
        skipped_count = len([company['symbol'] for company in companies]) - len(symbols) if not force_update else 0
        
        logger.info(f"データ更新完了: 成功 {success_count}, 失敗 {failed_count}, スキップ {skipped_count}")
        
        # 市場指数の結果も含めて報告
        market_success = sum(1 for success in market_results.values() if success)
        logger.info(f"市場指数更新: 成功 {market_success}, 合計 {len(MARKET_INDICES)}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total': len([company['symbol'] for company in companies]),
            'market_indices_success': market_success,
            'market_indices_total': len(MARKET_INDICES)
        }
    
    def update_specific_stocks(self, symbols: List[str]) -> Dict[str, bool]:
        """
        指定銘柄のみデータ更新
        """
        logger.info(f"指定銘柄データ更新: {len(symbols)} 銘柄")
        return self.collect_batch_stocks(symbols)

if __name__ == "__main__":
    collector = StockDataCollector()
    
    # テスト用: 特定銘柄のデータ収集
    test_symbols = ['7203', '6758', '9984']  # トヨタ、ソニーG、ソフトバンクG
    
    print("テスト用データ収集を開始...")
    results = collector.update_specific_stocks(test_symbols)
    
    print("結果:")
    for symbol, success in results.items():
        status = "成功" if success else "失敗"
        print(f"  {symbol}: {status}")
    
    # データベースの統計情報
    stats = collector.db_manager.get_database_stats()
    print(f"\nデータベース統計:")
    print(f"  企業数: {stats.get('companies_count', 0)}")
    print(f"  株価データ有り: {stats.get('symbols_with_prices', 0)}")
    print(f"  最新価格日付: {stats.get('latest_price_date', 'N/A')}")