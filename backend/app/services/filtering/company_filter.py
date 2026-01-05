import logging
from typing import Optional, cast

import yfinance as yf

from app.services.data.data_collector import StockDataCollector
from app.shared.config.settings import LOG_DATE_FORMAT, LOG_FORMAT, MIN_EMPLOYEES, MIN_REVENUE
from app.shared.database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


class CompanyFilter:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.data_collector = StockDataCollector()

    def get_company_info_from_yfinance(self, symbol: str) -> Optional[dict]:
        """
        yfinanceから企業の詳細情報を取得
        """
        formatted_symbol = self.data_collector.format_symbol(symbol)

        try:
            ticker = yf.Ticker(formatted_symbol)
            info = ticker.info

            if not info or "shortName" not in info:
                return None

            # 従業員数の取得
            employees = None
            for key in ["fullTimeEmployees", "employees"]:
                if key in info and info[key] is not None:
                    employees = int(info[key])
                    break

            # 売上高の取得
            revenue = None
            for key in ["totalRevenue", "revenue", "totalRevenues"]:
                if key in info and info[key] is not None:
                    revenue = int(info[key])
                    break

            # 時価総額の取得
            market_cap = None
            if "marketCap" in info and info["marketCap"] is not None:
                market_cap = int(info["marketCap"])

            # 業種の取得
            sector = info.get("sector", "")
            industry = info.get("industry", "")

            # 企業名
            company_name = info.get("longName") or info.get("shortName", "")

            return {
                "symbol": symbol,
                "name": company_name,
                "sector": sector,
                "industry": industry,
                "employees": employees,
                "revenue": revenue,
                "market_cap": market_cap,
                "country": info.get("country", ""),
                "website": info.get("website", ""),
                "business_summary": info.get("longBusinessSummary", ""),
            }

        except Exception as e:
            logger.warning(f"企業情報取得エラー {symbol}: {e}")
            return None

    def is_enterprise_company(self, company_info: dict) -> tuple[bool, str]:
        """
        企業がエンタープライズ企業かどうかを判定
        """
        reasons = []
        is_enterprise = True

        # 従業員数チェック
        employees = company_info.get("employees")
        if employees is not None:
            if employees < MIN_EMPLOYEES:
                is_enterprise = False
                reasons.append(f"従業員数不足: {employees} < {MIN_EMPLOYEES}")
            else:
                reasons.append(f"従業員数OK: {employees}")
        else:
            reasons.append("従業員数データなし")

        # 売上高チェック
        revenue = company_info.get("revenue")
        if revenue is not None:
            if revenue < MIN_REVENUE:
                is_enterprise = False
                reasons.append(f"売上高不足: {revenue:,} < {MIN_REVENUE:,}")
            else:
                reasons.append(f"売上高OK: {revenue:,}")
        else:
            reasons.append("売上高データなし")

        # 業種による判定
        sector = company_info.get("sector", "").lower()
        industry = company_info.get("industry", "").lower()

        # 除外業種
        excluded_sectors = [
            "real estate",
            "reits",
            "utilities",
            "mutual funds",
            "不動産",
            "リート",
            "ファンド",
            "投資",
        ]

        for excluded in excluded_sectors:
            if excluded in sector or excluded in industry:
                is_enterprise = False
                reasons.append(f"除外業種: {sector}/{industry}")
                break

        # 企業名による判定
        name = company_info.get("name", "").lower()
        excluded_name_keywords = [
            "reit",
            "fund",
            "investment",
            "holdings",
            "リート",
            "ファンド",
            "投資法人",
            "投資信託",
        ]

        for keyword in excluded_name_keywords:
            if keyword in name:
                is_enterprise = False
                reasons.append(f"除外企業名キーワード: {keyword}")
                break

        # 時価総額による補完判定
        market_cap = company_info.get("market_cap")
        if market_cap is not None:
            # 時価総額が100億円以上ならエンタープライズの可能性を上げる
            if market_cap >= 10_000_000_000:  # 100億円
                reasons.append(f"時価総額OK: {market_cap:,}")
                # 他の条件が不明な場合は時価総額で判定
                if employees is None and revenue is None:
                    is_enterprise = True
                    reasons.append("時価総額により判定")
            else:
                reasons.append(f"時価総額低い: {market_cap:,}")

        return is_enterprise, "; ".join(reasons)

    def update_company_enterprise_status(
        self, symbols: Optional[list[str]] = None, markets: Optional[list[str]] = None
    ) -> dict[str, dict]:
        """
        企業のエンタープライズステータスを更新
        """
        results = {}

        symbols = symbols or []
        markets = markets or []

        if not symbols:
            # データベースから全企業を取得（市場フィルタ適用）
            companies = self.db_manager.get_companies(markets=markets if markets else None)
            symbols = [company["symbol"] for company in companies]

        logger.info(f"企業情報更新開始: {len(symbols)} 銘柄")

        for i, symbol in enumerate(symbols):
            try:
                if (i + 1) % 20 == 0:
                    logger.info(f"進捗: {i + 1}/{len(symbols)}")

                # yfinanceから詳細情報を取得
                company_info = self.get_company_info_from_yfinance(symbol)
                if not company_info:
                    results[symbol] = {"success": False, "reason": "企業情報取得失敗"}
                    continue

                # エンタープライズ判定
                is_enterprise, reason = self.is_enterprise_company(company_info)

                # 既存の企業情報を取得して日本語名を保持
                existing_company = self.db_manager.get_company_by_symbol(symbol)

                # データベースの企業情報を更新
                update_data = {
                    "symbol": symbol,
                    "name": existing_company.get("name")
                    if existing_company
                    else company_info["name"],  # 既存の日本語名を保持
                    "sector": company_info.get("sector"),
                    "market": existing_company.get("market")
                    if existing_company
                    else None,  # 市場区分は既存データを保持
                    "employees": company_info.get("employees"),
                    "revenue": company_info.get("revenue"),
                    "is_enterprise": is_enterprise,
                }

                success = self.db_manager.insert_company(update_data)

                results[symbol] = {
                    "success": success,
                    "is_enterprise": is_enterprise,
                    "reason": reason,
                    "employees": company_info.get("employees"),
                    "revenue": company_info.get("revenue"),
                    "market_cap": company_info.get("market_cap"),
                }

                logger.debug(f"{symbol}: エンタープライズ={is_enterprise}, 理由={reason}")

            except Exception as e:
                logger.error(f"企業フィルタリングエラー {symbol}: {e}")
                results[symbol] = {"success": False, "reason": f"エラー: {e}"}

        # 結果の集計
        success_count = sum(1 for r in results.values() if r["success"])
        enterprise_count = sum(1 for r in results.values() if r.get("is_enterprise", False))

        logger.info(
            f"企業情報更新完了: 成功 {success_count}/{len(symbols)}, エンタープライズ {enterprise_count}"
        )

        return results

    def get_enterprise_companies(self) -> list[dict]:
        """
        エンタープライズ企業の一覧を取得
        """
        companies = cast(list[dict], self.db_manager.get_companies(is_enterprise_only=True))

        # 追加の統計情報を付与
        for company in companies:
            if company.get("employees"):
                if company["employees"] >= 10000:
                    company["size_category"] = "大企業"
                elif company["employees"] >= 5000:
                    company["size_category"] = "中堅企業"
                else:
                    company["size_category"] = "中小企業"
            else:
                company["size_category"] = "不明"

        return companies

    def get_filtering_stats(self) -> dict:
        """
        フィルタリングの統計情報を取得
        """
        try:
            all_companies = cast(list[dict], self.db_manager.get_companies())
            enterprise_companies = cast(list[dict], self.db_manager.get_companies(is_enterprise_only=True))

            # 従業員数による分類
            employee_stats = {
                "unknown": 0,
                "small": 0,  # < 1000
                "medium": 0,  # 1000-5000
                "large": 0,  # > 5000
            }

            # 売上高による分類
            revenue_stats = {
                "unknown": 0,
                "small": 0,  # < 100億
                "medium": 0,  # 100億-1000億
                "large": 0,  # > 1000億
            }

            for company in enterprise_companies:
                # 従業員数統計
                employees = company.get("employees")
                if employees is None:
                    employee_stats["unknown"] += 1
                elif employees < 1000:
                    employee_stats["small"] += 1
                elif employees < 5000:
                    employee_stats["medium"] += 1
                else:
                    employee_stats["large"] += 1

                # 売上高統計
                revenue = company.get("revenue")
                if revenue is None:
                    revenue_stats["unknown"] += 1
                elif revenue < 10_000_000_000:  # 100億
                    revenue_stats["small"] += 1
                elif revenue < 100_000_000_000:  # 1000億
                    revenue_stats["medium"] += 1
                else:
                    revenue_stats["large"] += 1

            # 業種統計
            sector_stats: dict[str, int] = {}
            for company in enterprise_companies:
                sector = company.get("sector", "Unknown")
                sector_stats[sector] = sector_stats.get(sector, 0) + 1

            return {
                "total_companies": len(all_companies),
                "enterprise_companies": len(enterprise_companies),
                "enterprise_ratio": len(enterprise_companies) / len(all_companies)
                if all_companies
                else 0,
                "employee_distribution": employee_stats,
                "revenue_distribution": revenue_stats,
                "sector_distribution": dict(
                    sorted(sector_stats.items(), key=lambda x: x[1], reverse=True)
                ),
            }

        except Exception as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {}


if __name__ == "__main__":
    filter_engine = CompanyFilter()

    # テスト用: 特定銘柄のフィルタリング
    test_symbols = ["7203", "6758", "9984", "1605"]  # 大手企業 + 中小企業のテスト

    print("企業フィルタリングテストを開始...")
    results = filter_engine.update_company_enterprise_status(test_symbols)

    print("\nフィルタリング結果:")
    for symbol, result in results.items():
        if result["success"]:
            status = "エンタープライズ" if result["is_enterprise"] else "非エンタープライズ"
            employees = result.get("employees", "不明")
            revenue = f"{result.get('revenue', 0):,}" if result.get("revenue") else "不明"
            print(f"  {symbol}: {status}")
            print(f"    従業員: {employees}, 売上: {revenue}")
            print(f"    理由: {result['reason']}")
        else:
            print(f"  {symbol}: 失敗 - {result['reason']}")

    # 統計情報の表示
    print("\nフィルタリング統計:")
    stats = filter_engine.get_filtering_stats()
    if stats:
        print(f"  総企業数: {stats['total_companies']}")
        print(f"  エンタープライズ企業数: {stats['enterprise_companies']}")
        print(f"  エンタープライズ比率: {stats['enterprise_ratio']:.2%}")

        print("  従業員規模分布:")
        for category, count in stats["employee_distribution"].items():
            print(f"    {category}: {count}")

        print("  売上規模分布:")
        for category, count in stats["revenue_distribution"].items():
            print(f"    {category}: {count}")

        print("  上位業種:")
        for sector, count in list(stats["sector_distribution"].items())[:5]:
            print(f"    {sector}: {count}")
