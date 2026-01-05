from datetime import datetime, timedelta
from typing import Optional, cast

import pandas as pd
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.shared.config.logging_config import get_service_logger
from app.shared.config.settings import DATABASE_PATH
from app.shared.database.models import Company, StockPrice, TechnicalIndicator, TickerInfo
from app.shared.database.session import SessionLocal, engine

logger = get_service_logger(__name__)


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None, session: Optional[Session] = None):
        """
        Args:
            db_path: データベースパス（後方互換性のため残すが使用しない）
            session: テスト用の外部セッション注入
        """
        self.db_path = db_path or DATABASE_PATH  # 後方互換性
        self._external_session = session
        self._engine = engine

    def _get_session(self) -> Session:
        """内部用セッション取得"""
        if self._external_session:
            return self._external_session
        return SessionLocal()

    def ensure_database_exists(self) -> None:
        """
        データベースの存在を確認
        注意: データベーススキーマはAlembicマイグレーションで管理されるようになりました。
        このメソッドは互換性のために残されていますが、何も実行しません。
        """
        pass

    def get_engine(self):
        """pandas用エンジン取得"""
        return self._engine

    # ========== 企業情報メソッド ==========

    def get_company_by_symbol(self, symbol: str) -> Optional[dict]:
        """指定された銘柄の企業情報を取得"""
        session = self._get_session()
        try:
            company = session.query(Company).filter_by(symbol=symbol).first()
            if company:
                return {
                    "symbol": company.symbol,
                    "name": company.name,
                    "sector": company.sector,
                    "market": company.market,
                    "employees": company.employees,
                    "revenue": company.revenue,
                    "is_enterprise": company.is_enterprise,
                    "dividend_yield": float(company.dividend_yield) if company.dividend_yield else None,
                    "last_updated": company.last_updated.isoformat() if company.last_updated else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting company {symbol}: {e}")
            return None
        finally:
            if not self._external_session:
                session.close()

    def get_companies(
        self, is_enterprise_only: bool = False, markets: Optional[list[str]] = None
    ) -> list[dict]:
        """企業情報一覧を取得"""
        session = self._get_session()
        try:
            query = session.query(Company)

            if is_enterprise_only:
                query = query.filter(Company.is_enterprise.is_(True))

            if markets:
                query = query.filter(Company.market.in_(markets))

            companies = query.all()
            return [
                {
                    "symbol": c.symbol,
                    "name": c.name,
                    "sector": c.sector,
                    "market": c.market,
                    "employees": c.employees,
                    "revenue": c.revenue,
                    "is_enterprise": c.is_enterprise,
                    "dividend_yield": float(c.dividend_yield) if c.dividend_yield else None,
                    "last_updated": c.last_updated.isoformat() if c.last_updated else None,
                }
                for c in companies
            ]
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return []
        finally:
            if not self._external_session:
                session.close()

    def insert_company(self, company_data: dict) -> bool:
        """企業情報を挿入または更新（UPSERT）"""
        session = self._get_session()
        try:
            existing = session.query(Company).filter_by(symbol=company_data["symbol"]).first()

            if existing:
                # UPDATE
                existing.name = company_data["name"]
                existing.sector = company_data.get("sector")
                existing.market = company_data.get("market")
                existing.employees = company_data.get("employees")
                existing.revenue = company_data.get("revenue")
                existing.is_enterprise = company_data.get("is_enterprise", False)
                existing.dividend_yield = company_data.get("dividend_yield")
                existing.last_updated = datetime.now()
            else:
                # INSERT
                company = Company(
                    symbol=company_data["symbol"],
                    name=company_data["name"],
                    sector=company_data.get("sector"),
                    market=company_data.get("market"),
                    employees=company_data.get("employees"),
                    revenue=company_data.get("revenue"),
                    is_enterprise=company_data.get("is_enterprise", False),
                    dividend_yield=company_data.get("dividend_yield"),
                    last_updated=datetime.now(),
                )
                session.add(company)

            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting company {company_data.get('symbol')}: {e}")
            session.rollback()
            return False
        finally:
            if not self._external_session:
                session.close()

    def insert_companies(self, companies_data: list[dict]) -> bool:
        """複数の企業データを一括挿入"""
        session = self._get_session()
        success_count = 0

        try:
            for company_data in companies_data:
                try:
                    existing = session.query(Company).filter_by(symbol=company_data["symbol"]).first()

                    if existing:
                        # UPDATE
                        existing.name = company_data["name"]
                        existing.sector = company_data.get("sector")
                        existing.market = company_data.get("market")
                        existing.employees = company_data.get("employees")
                        existing.revenue = company_data.get("revenue")
                        existing.is_enterprise = company_data.get("is_enterprise", False)
                        existing.dividend_yield = company_data.get("dividend_yield")
                        existing.last_updated = datetime.now()
                    else:
                        # INSERT
                        company = Company(
                            symbol=company_data["symbol"],
                            name=company_data["name"],
                            sector=company_data.get("sector"),
                            market=company_data.get("market"),
                            employees=company_data.get("employees"),
                            revenue=company_data.get("revenue"),
                            is_enterprise=company_data.get("is_enterprise", False),
                            dividend_yield=company_data.get("dividend_yield"),
                            last_updated=datetime.now(),
                        )
                        session.add(company)

                    success_count += 1
                except Exception as e:
                    logger.error(f"Error processing company {company_data.get('symbol')}: {e}")
                    continue

            session.commit()
            logger.info(f"企業データ一括挿入完了: 成功 {success_count}/{len(companies_data)}")
            return success_count > 0

        except Exception as e:
            logger.error(f"企業データ一括挿入エラー: {e}")
            session.rollback()
            return False
        finally:
            if not self._external_session:
                session.close()

    def get_filtered_companies(
        self,
        divergence_min: Optional[float] = None,
        divergence_max: Optional[float] = None,
        dividend_yield_min: Optional[float] = None,
        dividend_yield_max: Optional[float] = None,
        is_enterprise_only: bool = True,
        market_filter: Optional[str] = None,
    ) -> list[dict]:
        """複雑なフィルタ条件で企業を検索"""
        session = self._get_session()
        try:
            # サブクエリ: 各銘柄の最新日付
            latest_dates_subq = (
                session.query(
                    TechnicalIndicator.symbol,
                    func.max(TechnicalIndicator.date).label("max_date")
                )
                .group_by(TechnicalIndicator.symbol)
                .subquery()
            )

            # メインクエリ
            query = session.query(
                Company, TechnicalIndicator
            ).join(
                TechnicalIndicator, Company.symbol == TechnicalIndicator.symbol
            ).join(
                latest_dates_subq,
                (TechnicalIndicator.symbol == latest_dates_subq.c.symbol) &
                (TechnicalIndicator.date == latest_dates_subq.c.max_date)
            )

            # フィルタ適用
            if is_enterprise_only:
                query = query.filter(Company.is_enterprise.is_(True))

            if divergence_min is not None:
                query = query.filter(func.abs(TechnicalIndicator.divergence_rate) >= divergence_min)

            if divergence_max is not None:
                query = query.filter(TechnicalIndicator.divergence_rate <= divergence_max)

            if dividend_yield_min is not None:
                query = query.filter(
                    TechnicalIndicator.dividend_yield.isnot(None),
                    TechnicalIndicator.dividend_yield >= dividend_yield_min
                )

            if dividend_yield_max is not None:
                query = query.filter(
                    TechnicalIndicator.dividend_yield.isnot(None),
                    TechnicalIndicator.dividend_yield <= dividend_yield_max
                )

            if market_filter is not None:
                query = query.filter(Company.market == market_filter)

            results = query.distinct().all()

            # dict化（後方互換性）
            return [
                {
                    "symbol": row.Company.symbol,
                    "name": row.Company.name,
                    "sector": row.Company.sector,
                    "market": row.Company.market,
                    "employees": row.Company.employees,
                    "revenue": row.Company.revenue,
                    "is_enterprise": row.Company.is_enterprise,
                    "last_updated": row.Company.last_updated.isoformat() if row.Company.last_updated else None,
                    "divergence_rate": float(row.TechnicalIndicator.divergence_rate) if row.TechnicalIndicator.divergence_rate else None,
                    "dividend_yield": float(row.TechnicalIndicator.dividend_yield) if row.TechnicalIndicator.dividend_yield else None,
                    "date": row.TechnicalIndicator.date.isoformat() if row.TechnicalIndicator.date else None,
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error getting filtered companies: {e}")
            return []
        finally:
            if not self._external_session:
                session.close()

    # ========== 株価データメソッド ==========

    def get_latest_stock_price_date(self, symbol: str) -> Optional[datetime]:
        """指定された銘柄の最新株価データの日付を取得"""
        session = self._get_session()
        try:
            result = session.query(func.max(StockPrice.date)).filter_by(symbol=symbol).scalar()
            if result:
                # Dateオブジェクトをdatetimeに変換
                return datetime.combine(result, datetime.min.time())
            return None
        except Exception as e:
            logger.error(f"Error fetching latest price date for {symbol}: {e}")
            return None
        finally:
            if not self._external_session:
                session.close()

    def get_latest_price_dates(self, symbols: list[str]) -> dict[str, Optional[datetime]]:
        """複数銘柄の最新株価日付をまとめて取得"""
        session = self._get_session()
        latest_dates = {}
        try:
            results = session.query(
                StockPrice.symbol,
                func.max(StockPrice.date).label("max_date")
            ).filter(StockPrice.symbol.in_(symbols)).group_by(StockPrice.symbol).all()

            for row in results:
                # Dateオブジェクトをdatetimeに変換
                latest_dates[row.symbol] = datetime.combine(row.max_date, datetime.min.time()) if row.max_date else None

            return latest_dates
        except Exception as e:
            logger.error(f"Error fetching latest price dates for {symbols}: {e}")
            return latest_dates
        finally:
            if not self._external_session:
                session.close()

    def get_stock_prices(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """株価データ取得（pandas read_sql使用）"""
        try:
            query = "SELECT * FROM stock_prices WHERE symbol = :symbol"
            params = {"symbol": symbol}

            if start_date:
                query += " AND date >= :start_date"
                params["start_date"] = start_date

            if end_date:
                query += " AND date <= :end_date"
                params["end_date"] = end_date

            query += " ORDER BY date"

            # pandas read_sql（SQLAlchemyエンジン使用）
            df = pd.read_sql(query, self._engine, params=params)

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)

            return df
        except Exception as e:
            logger.error(f"Error getting stock prices for {symbol}: {e}")
            return pd.DataFrame()

    def insert_stock_prices(self, symbol: str, price_data: pd.DataFrame) -> bool:
        """株価データ挿入（pandas to_sql使用）"""
        session = self._get_session()
        try:
            # 既存データ削除（SQLAlchemy）
            session.query(StockPrice).filter_by(symbol=symbol).delete()
            session.commit()  # 削除を即座にコミット

            # DataFrameの準備
            data_copy = price_data.copy()
            data_copy["symbol"] = symbol
            # DatetimeIndexを文字列に変換
            datetime_index = pd.to_datetime(data_copy.index)
            data_copy.index = datetime_index.strftime("%Y-%m-%d")
            data_copy.reset_index(inplace=True)
            data_copy.rename(columns={"index": "date"}, inplace=True)

            # pandas to_sql（SQLAlchemyエンジン使用）
            data_copy.to_sql("stock_prices", self._engine, if_exists="append", index=False)

            return True
        except Exception as e:
            logger.error(f"Error inserting stock prices for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            if not self._external_session:
                session.close()

    # ========== テクニカル指標メソッド ==========

    def get_technical_indicators(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """テクニカル指標取得（pandas read_sql使用）"""
        try:
            query = "SELECT * FROM technical_indicators WHERE symbol = :symbol"
            params = {"symbol": symbol}

            if start_date:
                query += " AND date >= :start_date"
                params["start_date"] = start_date

            if end_date:
                query += " AND date <= :end_date"
                params["end_date"] = end_date

            query += " ORDER BY date"

            # pandas read_sql（SQLAlchemyエンジン使用）
            df = pd.read_sql(query, self._engine, params=params)

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)

            return df
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {e}")
            return pd.DataFrame()

    def insert_technical_indicators(self, symbol: str, indicators_data: pd.DataFrame) -> bool:
        """テクニカル指標挿入（pandas to_sql使用）"""
        session = self._get_session()
        try:
            # 既存データ削除（SQLAlchemy）
            session.query(TechnicalIndicator).filter_by(symbol=symbol).delete()
            session.commit()  # 削除を即座にコミット

            # DataFrameの準備
            data_copy = indicators_data.copy()
            data_copy["symbol"] = symbol
            # DatetimeIndexを文字列に変換
            datetime_index = pd.to_datetime(data_copy.index)
            data_copy.index = datetime_index.strftime("%Y-%m-%d")
            data_copy.reset_index(inplace=True)
            data_copy.rename(columns={"index": "date"}, inplace=True)

            # pandas to_sql（SQLAlchemyエンジン使用）
            data_copy.to_sql("technical_indicators", self._engine, if_exists="append", index=False)

            return True
        except Exception as e:
            logger.error(f"Error inserting technical indicators for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            if not self._external_session:
                session.close()

    # ========== ティッカー情報メソッド ==========

    def get_ticker_info(self, symbol: str) -> Optional[dict]:
        """ティッカー情報を取得"""
        session = self._get_session()
        try:
            ticker = session.query(TickerInfo).filter_by(symbol=symbol).first()
            if ticker:
                return {
                    "symbol": ticker.symbol,
                    "industry": ticker.industry,
                    "sector": ticker.sector,
                    "full_time_employees": ticker.full_time_employees,
                    "market_cap": ticker.market_cap,
                    "current_price": float(ticker.current_price) if ticker.current_price else None,
                    "dividend_yield": float(ticker.dividend_yield) if ticker.dividend_yield else None,
                    "dividend_rate": float(ticker.dividend_rate) if ticker.dividend_rate else None,
                    "trailing_annual_dividend_rate": float(ticker.trailing_annual_dividend_rate) if ticker.trailing_annual_dividend_rate else None,
                    "ex_dividend_date": ticker.ex_dividend_date.isoformat() if ticker.ex_dividend_date else None,
                    "trailing_pe": float(ticker.trailing_pe) if ticker.trailing_pe else None,
                    "forward_pe": float(ticker.forward_pe) if ticker.forward_pe else None,
                    "price_to_book": float(ticker.price_to_book) if ticker.price_to_book else None,
                    "debt_to_equity": float(ticker.debt_to_equity) if ticker.debt_to_equity else None,
                    "return_on_equity": float(ticker.return_on_equity) if ticker.return_on_equity else None,
                    "return_on_assets": float(ticker.return_on_assets) if ticker.return_on_assets else None,
                    "total_revenue": ticker.total_revenue,
                    "earnings_growth": float(ticker.earnings_growth) if ticker.earnings_growth else None,
                    "revenue_growth": float(ticker.revenue_growth) if ticker.revenue_growth else None,
                    "profit_margins": float(ticker.profit_margins) if ticker.profit_margins else None,
                    "fifty_two_week_high": float(ticker.fifty_two_week_high) if ticker.fifty_two_week_high else None,
                    "fifty_two_week_low": float(ticker.fifty_two_week_low) if ticker.fifty_two_week_low else None,
                    "average_volume": ticker.average_volume,
                    "corporate_actions_dividend": ticker.corporate_actions_dividend,
                    "last_updated": ticker.last_updated.isoformat() if ticker.last_updated else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting ticker info for {symbol}: {e}")
            return None
        finally:
            if not self._external_session:
                session.close()

    def get_latest_ticker_info_date(self, symbol: str) -> Optional[datetime]:
        """指定された銘柄の最新ticker_info更新日を取得"""
        session = self._get_session()
        try:
            ticker = session.query(TickerInfo).filter_by(symbol=symbol).first()
            if ticker and ticker.last_updated:
                return cast(datetime, ticker.last_updated)
            return None
        except Exception as e:
            logger.error(f"Error fetching latest ticker info date for {symbol}: {e}")
            return None
        finally:
            if not self._external_session:
                session.close()

    def get_latest_ticker_info_dates(self, symbols: list[str]) -> dict[str, Optional[datetime]]:
        """指定された銘柄のticker_infoの最終更新日を取得"""
        session = self._get_session()
        latest_dates = {}
        try:
            results = session.query(
                TickerInfo.symbol,
                TickerInfo.last_updated
            ).filter(TickerInfo.symbol.in_(symbols)).all()

            for row in results:
                latest_dates[row.symbol] = row.last_updated

            return latest_dates
        except Exception as e:
            logger.error(f"Error fetching latest ticker info dates for {symbols}: {e}")
            return latest_dates
        finally:
            if not self._external_session:
                session.close()

    def insert_ticker_info(self, symbol: str, ticker_info: dict) -> bool:
        """ティッカー情報をデータベースに保存（UPSERT）"""
        session = self._get_session()
        try:
            # corporateActionsの配当情報を抽出
            dividend_actions = []
            if 'corporateActions' in ticker_info:
                for action in ticker_info['corporateActions']:
                    if action.get('header') == 'Dividend' and 'meta' in action:
                        dividend_actions.append(action['meta'])

            existing = session.query(TickerInfo).filter_by(symbol=symbol).first()

            if existing:
                # UPDATE
                existing.industry = ticker_info.get("industry")
                existing.sector = ticker_info.get("sector")
                existing.full_time_employees = ticker_info.get("fullTimeEmployees")
                existing.market_cap = ticker_info.get("marketCap")
                existing.current_price = ticker_info.get("currentPrice")
                existing.dividend_yield = ticker_info.get("dividendYield")
                existing.dividend_rate = ticker_info.get("dividendRate")
                existing.trailing_annual_dividend_rate = ticker_info.get("trailingAnnualDividendRate")
                existing.ex_dividend_date = datetime.fromtimestamp(ticker_info.get("exDividendDate", 0)) if ticker_info.get("exDividendDate") else None
                existing.trailing_pe = ticker_info.get("trailingPE")
                existing.forward_pe = ticker_info.get("forwardPE")
                existing.price_to_book = ticker_info.get("priceToBook")
                existing.debt_to_equity = ticker_info.get("debtToEquity")
                existing.return_on_equity = ticker_info.get("returnOnEquity")
                existing.return_on_assets = ticker_info.get("returnOnAssets")
                existing.total_revenue = ticker_info.get("totalRevenue")
                existing.earnings_growth = ticker_info.get("earningsGrowth")
                existing.revenue_growth = ticker_info.get("revenueGrowth")
                existing.profit_margins = ticker_info.get("profitMargins")
                existing.fifty_two_week_high = ticker_info.get("fiftyTwoWeekHigh")
                existing.fifty_two_week_low = ticker_info.get("fiftyTwoWeekLow")
                existing.average_volume = ticker_info.get("averageVolume")
                existing.corporate_actions_dividend = str(dividend_actions) if dividend_actions else None
                existing.last_updated = datetime.now()
            else:
                # INSERT
                new_ticker = TickerInfo(
                    symbol=symbol,
                    industry=ticker_info.get("industry"),
                    sector=ticker_info.get("sector"),
                    full_time_employees=ticker_info.get("fullTimeEmployees"),
                    market_cap=ticker_info.get("marketCap"),
                    current_price=ticker_info.get("currentPrice"),
                    dividend_yield=ticker_info.get("dividendYield"),
                    dividend_rate=ticker_info.get("dividendRate"),
                    trailing_annual_dividend_rate=ticker_info.get("trailingAnnualDividendRate"),
                    ex_dividend_date=datetime.fromtimestamp(ticker_info.get("exDividendDate", 0)) if ticker_info.get("exDividendDate") else None,
                    trailing_pe=ticker_info.get("trailingPE"),
                    forward_pe=ticker_info.get("forwardPE"),
                    price_to_book=ticker_info.get("priceToBook"),
                    debt_to_equity=ticker_info.get("debtToEquity"),
                    return_on_equity=ticker_info.get("returnOnEquity"),
                    return_on_assets=ticker_info.get("returnOnAssets"),
                    total_revenue=ticker_info.get("totalRevenue"),
                    earnings_growth=ticker_info.get("earningsGrowth"),
                    revenue_growth=ticker_info.get("revenueGrowth"),
                    profit_margins=ticker_info.get("profitMargins"),
                    fifty_two_week_high=ticker_info.get("fiftyTwoWeekHigh"),
                    fifty_two_week_low=ticker_info.get("fiftyTwoWeekLow"),
                    average_volume=ticker_info.get("averageVolume"),
                    corporate_actions_dividend=str(dividend_actions) if dividend_actions else None,
                    last_updated=datetime.now(),
                )
                session.add(new_ticker)

            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting ticker info for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            if not self._external_session:
                session.close()

    def get_symbols_needing_ticker_update(self, days_old: int = 30) -> list[str]:
        """ティッカー情報の更新が必要な銘柄一覧を取得（月1更新用）"""
        session = self._get_session()
        try:
            threshold_date = datetime.now() - timedelta(days=days_old)

            results = session.query(Company.symbol).outerjoin(
                TickerInfo, Company.symbol == TickerInfo.symbol
            ).filter(
                or_(
                    TickerInfo.last_updated.is_(None),
                    TickerInfo.last_updated < threshold_date
                )
            ).all()

            return [row.symbol for row in results]
        except Exception as e:
            logger.error(f"Error getting symbols needing ticker update: {e}")
            return []
        finally:
            if not self._external_session:
                session.close()

    # ========== ユーティリティメソッド ==========

    def delete_old_data(self, symbol: str, table: str, days_to_keep: int = 365) -> None:
        """古いデータを削除"""
        session = self._get_session()
        try:
            threshold_date = datetime.now() - timedelta(days=days_to_keep)

            if table == "stock_prices":
                session.query(StockPrice).filter(
                    StockPrice.symbol == symbol,
                    StockPrice.date < threshold_date
                ).delete()
            elif table == "technical_indicators":
                session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.symbol == symbol,
                    TechnicalIndicator.date < threshold_date
                ).delete()

            session.commit()
            logger.info(f"Old data deleted for {symbol} from {table}")
        except Exception as e:
            logger.error(f"Error deleting old data for {symbol}: {e}")
            session.rollback()
        finally:
            if not self._external_session:
                session.close()

    def get_database_stats(self) -> dict:
        """データベース統計情報を取得"""
        session = self._get_session()
        try:
            companies_count = session.query(func.count(Company.symbol)).scalar()

            symbols_with_prices = session.query(func.count(func.distinct(StockPrice.symbol))).scalar()

            symbols_with_indicators = session.query(func.count(func.distinct(TechnicalIndicator.symbol))).scalar()

            symbols_with_ticker_info = session.query(func.count(func.distinct(TickerInfo.symbol))).scalar()

            latest_price_date = session.query(func.max(StockPrice.date)).scalar()

            latest_ticker_update = session.query(func.max(TickerInfo.last_updated)).scalar()

            return {
                "companies_count": companies_count or 0,
                "symbols_with_prices": symbols_with_prices or 0,
                "symbols_with_indicators": symbols_with_indicators or 0,
                "symbols_with_ticker_info": symbols_with_ticker_info or 0,
                "latest_price_date": latest_price_date.isoformat() if latest_price_date else None,
                "latest_ticker_update": latest_ticker_update.isoformat() if latest_ticker_update else None,
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            if not self._external_session:
                session.close()
