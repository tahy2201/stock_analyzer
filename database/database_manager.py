import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from config.settings import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DATABASE_PATH
        self.ensure_database_exists()

    def ensure_database_exists(self) -> None:
        from database.models import create_tables

        create_tables()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_latest_price_dates(self, symbols: list[str]) -> dict[str, Optional[datetime]]:
        latest_dates = {}
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT symbol, MAX(date) FROM stock_prices WHERE symbol IN ({','.join(['?'] * len(symbols))}) GROUP BY symbol",
                    symbols
                )
                rows = cursor.fetchall()
                for row in rows:
                    latest_dates[row["symbol"]] = datetime.fromisoformat(row[1]) if row[1] else None
        except Exception as e:
            logger.error(f"Error fetching latest price dates for {symbols}: {e}")
        return latest_dates

    def get_latest_ticker_info_dates(self, symbols: list[str]) -> dict[str, Optional[datetime]]:
        """
        指定された銘柄のticker_infoの最終更新日を取得
        """
        latest_dates = {}
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT symbol, MAX(last_updated) FROM ticker_info WHERE symbol IN ({','.join(['?'] * len(symbols))}) GROUP BY symbol",
                    symbols
                )
                rows = cursor.fetchall()
                for row in rows:
                    latest_dates[row["symbol"]] = datetime.fromisoformat(row[1]) if row[1] else None
        except Exception as e:
            logger.error(f"Error fetching latest ticker info dates for {symbols}: {e}")
        return latest_dates

    def insert_company(self, company_data: Dict) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO companies 
                    (symbol, name, sector, market, employees, revenue, is_enterprise, dividend_yield, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        company_data["symbol"],
                        company_data["name"],
                        company_data.get("sector"),
                        company_data.get("market"),
                        company_data.get("employees"),
                        company_data.get("revenue"),
                        company_data.get("is_enterprise", False),
                        company_data.get("dividend_yield"),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting company {company_data.get('symbol')}: {e}")
            return False

    def insert_stock_prices(self, symbol: str, price_data: pd.DataFrame) -> bool:
        try:
            with self.get_connection() as conn:
                # データの準備
                data_copy = price_data.copy()
                data_copy["symbol"] = symbol
                data_copy.index = data_copy.index.strftime("%Y-%m-%d")
                data_copy.reset_index(inplace=True)
                data_copy.rename(columns={"Date": "date"}, inplace=True)

                # 既存データの削除（同じシンボルのデータ）
                cursor = conn.cursor()
                cursor.execute("DELETE FROM stock_prices WHERE symbol = ?", (symbol,))

                # 新しいデータの挿入
                data_copy.to_sql("stock_prices", conn, if_exists="append", index=False)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting stock prices for {symbol}: {e}")
            return False

    def insert_technical_indicators(self, symbol: str, indicators_data: pd.DataFrame) -> bool:
        try:
            with self.get_connection() as conn:
                # データの準備
                data_copy = indicators_data.copy()
                data_copy["symbol"] = symbol
                data_copy.index = data_copy.index.strftime("%Y-%m-%d")
                data_copy.reset_index(inplace=True)
                data_copy.rename(columns={"Date": "date"}, inplace=True)

                # 既存データの削除（同じシンボルのデータ）
                cursor = conn.cursor()
                cursor.execute("DELETE FROM technical_indicators WHERE symbol = ?", (symbol,))

                # 新しいデータの挿入
                data_copy.to_sql("technical_indicators", conn, if_exists="append", index=False)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting technical indicators for {symbol}: {e}")
            return False

    def get_companies(
        self, is_enterprise_only: bool = False, markets: Optional[List[str]] = None
    ) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM companies"
                conditions = []

                if is_enterprise_only:
                    conditions.append("is_enterprise = 1")

                if markets:
                    market_placeholders = ",".join(["?" for _ in markets])
                    conditions.append(f"market IN ({market_placeholders})")

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                cursor = conn.cursor()
                params = markets if markets else []
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return []

    def get_company_by_symbol(self, symbol: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM companies WHERE symbol = ?", (symbol,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting company {symbol}: {e}")
            return None

    def get_stock_prices(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM stock_prices WHERE symbol = ?"
                params = [symbol]

                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date)

                query += " ORDER BY date"

                df = pd.read_sql_query(query, conn, params=params)
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)
                return df
        except Exception as e:
            logger.error(f"Error getting stock prices for {symbol}: {e}")
            return pd.DataFrame()

    def get_technical_indicators(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM technical_indicators WHERE symbol = ?"
                params = [symbol]

                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date)

                query += " ORDER BY date"

                df = pd.read_sql_query(query, conn, params=params)
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)
                return df
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {e}")
            return pd.DataFrame()

    def get_filtered_companies(
        self,
        divergence_min: Optional[float] = None,
        divergence_max: Optional[float] = None,
        dividend_yield_min: Optional[float] = None,
        dividend_yield_max: Optional[float] = None,
        is_enterprise_only: bool = True,
    ) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT DISTINCT c.*, ti.divergence_rate, ti.dividend_yield, ti.date
                    FROM companies c
                    JOIN technical_indicators ti ON c.symbol = ti.symbol
                    WHERE ti.date = (
                        SELECT MAX(date) FROM technical_indicators ti2 
                        WHERE ti2.symbol = c.symbol
                    )
                """
                params = []

                if is_enterprise_only:
                    query += " AND c.is_enterprise = 1"

                if divergence_min is not None:
                    query += " AND ABS(ti.divergence_rate) >= ?"
                    params.append(divergence_min)

                if divergence_max is not None:
                    query += " AND ABS(ti.divergence_rate) <= ?"
                    params.append(divergence_max)

                if dividend_yield_min is not None:
                    query += " AND ti.dividend_yield >= ?"
                    params.append(dividend_yield_min)

                if dividend_yield_max is not None:
                    query += " AND ti.dividend_yield <= ?"
                    params.append(dividend_yield_max)

                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting filtered companies: {e}")
            return []

    def delete_old_data(self, symbol: str, table: str, days_to_keep: int = 365):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    DELETE FROM {table} 
                    WHERE symbol = ? AND date < date('now', '-{days_to_keep} days')
                """,
                    (symbol,),
                )
                conn.commit()
                logger.info(f"Old data deleted for {symbol} from {table}")
        except Exception as e:
            logger.error(f"Error deleting old data for {symbol}: {e}")

    def insert_ticker_info(self, symbol: str, ticker_info: Dict) -> bool:
        """
        ティッカー情報をデータベースに保存
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # corporateActionsの配当情報を抽出
                dividend_actions = []
                if 'corporateActions' in ticker_info:
                    for action in ticker_info['corporateActions']:
                        if action.get('header') == 'Dividend' and 'meta' in action:
                            dividend_actions.append(action['meta'])

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO ticker_info
                    (symbol, industry, sector, full_time_employees, market_cap, current_price,
                     dividend_yield, dividend_rate, trailing_annual_dividend_rate, ex_dividend_date,
                     trailing_pe, forward_pe, price_to_book, debt_to_equity, return_on_equity,
                     return_on_assets, total_revenue, earnings_growth, revenue_growth, profit_margins,
                     fifty_two_week_high, fifty_two_week_low, average_volume, corporate_actions_dividend,
                     last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        symbol,
                        ticker_info.get("industry"),
                        ticker_info.get("sector"),
                        ticker_info.get("fullTimeEmployees"),
                        ticker_info.get("marketCap"),
                        ticker_info.get("currentPrice"),
                        ticker_info.get("dividendYield"),
                        ticker_info.get("dividendRate"),
                        ticker_info.get("trailingAnnualDividendRate"),
                        datetime.fromtimestamp(ticker_info.get("exDividendDate", 0)).date() if ticker_info.get("exDividendDate") else None,
                        ticker_info.get("trailingPE"),
                        ticker_info.get("forwardPE"),
                        ticker_info.get("priceToBook"),
                        ticker_info.get("debtToEquity"),
                        ticker_info.get("returnOnEquity"),
                        ticker_info.get("returnOnAssets"),
                        ticker_info.get("totalRevenue"),
                        ticker_info.get("earningsGrowth"),
                        ticker_info.get("revenueGrowth"),
                        ticker_info.get("profitMargins"),
                        ticker_info.get("fiftyTwoWeekHigh"),
                        ticker_info.get("fiftyTwoWeekLow"),
                        ticker_info.get("averageVolume"),
                        str(dividend_actions) if dividend_actions else None,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting ticker info for {symbol}: {e}")
            return False

    def get_ticker_info(self, symbol: str) -> Optional[Dict]:
        """
        ティッカー情報を取得
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ticker_info WHERE symbol = ?", (symbol,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting ticker info for {symbol}: {e}")
            return None

    def get_symbols_needing_ticker_update(self, days_old: int = 30) -> List[str]:
        """
        ティッカー情報の更新が必要な銘柄一覧を取得（月1更新用）
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT c.symbol
                    FROM companies c
                    LEFT JOIN ticker_info ti ON c.symbol = ti.symbol
                    WHERE ti.last_updated IS NULL
                       OR ti.last_updated < datetime('now', '-{} days')
                    """.format(days_old)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting symbols needing ticker update: {e}")
            return []

    def get_database_stats(self) -> Dict:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM companies")
                companies_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_prices")
                symbols_with_prices = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM technical_indicators")
                symbols_with_indicators = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ticker_info")
                symbols_with_ticker_info = cursor.fetchone()[0]

                cursor.execute("SELECT MAX(date) FROM stock_prices")
                latest_price_date = cursor.fetchone()[0]

                cursor.execute("SELECT MAX(last_updated) FROM ticker_info")
                latest_ticker_update = cursor.fetchone()[0]

                return {
                    "companies_count": companies_count,
                    "symbols_with_prices": symbols_with_prices,
                    "symbols_with_indicators": symbols_with_indicators,
                    "symbols_with_ticker_info": symbols_with_ticker_info,
                    "latest_price_date": latest_price_date,
                    "latest_ticker_update": latest_ticker_update,
                }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
