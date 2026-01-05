import logging
from typing import Optional

from app.config.models import FilterCriteria
from app.config.settings import LOG_DATE_FORMAT, LOG_FORMAT
from app.database.database_manager import DatabaseManager
from app.database.models import Company
from app.database.session import get_db

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


class CompanyFilterService:
    """企業フィルタリングを担当するサービスクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

    def filter_companies(self, filter_criteria: FilterCriteria) -> list[str]:
        """
        フィルタ条件に基づいて企業を抽出
        """
        try:
            logger.info(f"企業フィルタリング開始: {filter_criteria}")

            # 特定銘柄が指定されている場合は、それらのみを返す
            if filter_criteria.specific_symbols:
                logger.info(f"特定銘柄フィルタ適用: {filter_criteria.specific_symbols}")
                # 指定された銘柄がデータベースに存在するかチェック
                valid_symbols = []
                for symbol in filter_criteria.specific_symbols:
                    if self.get_company_info(symbol):
                        valid_symbols.append(symbol)
                    else:
                        logger.warning(f"銘柄 {symbol} はデータベースに存在しません")

                logger.info(f"特定銘柄フィルタリング完了: {len(valid_symbols)} 銘柄")
                return valid_symbols

            # 通常のフィルタリング処理
            # marketsが指定されている場合、最初のマーケットのみ適用（複数指定には未対応）
            market_filter = None
            if filter_criteria.markets and len(filter_criteria.markets) > 0:
                market_filter = filter_criteria.markets[0]
                logger.info(f"市場フィルタ適用: {market_filter}")

            companies = self.db_manager.get_filtered_companies(
                divergence_min=filter_criteria.divergence_min,
                dividend_yield_min=filter_criteria.dividend_yield_min,
                dividend_yield_max=filter_criteria.dividend_yield_max,
                is_enterprise_only=filter_criteria.is_enterprise_only,
                market_filter=market_filter
            )

            symbols = [company["symbol"] for company in companies]
            logger.info(f"フィルタリング完了: {len(symbols)} 銘柄が抽出されました")

            return symbols

        except Exception as e:
            logger.error(f"企業フィルタリングエラー: {e}")
            return []

    def get_company_info(self, symbol: str) -> Optional[dict]:
        """
        企業の基本情報を取得
        """
        try:
            return self.db_manager.get_company_by_symbol(symbol)

        except Exception as e:
            logger.error(f"企業情報取得エラー {symbol}: {e}")
            return None

    def get_all_companies(self, limit: Optional[int] = None) -> list[dict]:
        """
        全企業リストを取得
        """
        try:
            # companiesテーブルから直接全企業を取得（technical_indicatorsとJOINしない）
            companies = self.db_manager.get_companies(is_enterprise_only=False)

            # limit適用
            if limit:
                companies = companies[:limit]

            logger.info(f"企業リスト取得完了: {len(companies)} 件")
            return companies

        except Exception as e:
            logger.error(f"企業リスト取得エラー: {e}")
            return []

    def search_companies(
        self,
        search: str,
        limit: int = 100,
        market: Optional[str] = None,
        sector: Optional[str] = None,
        is_enterprise: Optional[bool] = None,
    ) -> list[dict]:
        """
        銘柄コードまたは銘柄名で企業を検索する（データベースレベル）。

        Args:
            search: 検索文字列（銘柄コードまたは銘柄名の部分一致）
            limit: 取得件数の上限
            market: 市場区分でフィルタ（オプション）
            sector: 業種でフィルタ（オプション）
            is_enterprise: 大企業のみ（オプション）

        Returns:
            検索結果の企業リスト
        """
        try:
            db = next(get_db())
            try:
                # 検索条件を構築（銘柄コードまたは銘柄名で部分一致）
                search_pattern = f"%{search}%"
                query = db.query(Company).filter(
                    (Company.symbol.ilike(search_pattern))
                    | (Company.name.ilike(search_pattern))
                )

                # 追加フィルタ適用
                if market:
                    query = query.filter(Company.market == market)
                if sector:
                    query = query.filter(Company.sector == sector)
                if is_enterprise is not None:
                    query = query.filter(Company.is_enterprise.is_(is_enterprise))

                # limit適用
                companies = query.limit(limit).all()

                # 辞書形式に変換
                result = [
                    {
                        "symbol": c.symbol,
                        "name": c.name,
                        "sector": c.sector,
                        "market": c.market,
                        "is_enterprise": c.is_enterprise,
                    }
                    for c in companies
                ]

                logger.info(f"検索完了: '{search}' で {len(result)} 件")
                return result
            finally:
                db.close()

        except Exception as e:
            logger.error(f"企業検索エラー: {e}")
            return []
