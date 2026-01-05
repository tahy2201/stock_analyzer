"""CompanyFilterService unit tests."""

import pytest

from app.services.filtering.company_filter_service import CompanyFilterService
from app.shared.database import models


@pytest.fixture
def company_filter_service(db_session):
    """CompanyFilterServiceのインスタンスを提供。"""
    return CompanyFilterService()


@pytest.fixture
def test_companies(db_session):
    """テスト用企業データを複数作成。"""
    companies = [
        models.Company(symbol="1234", name="テスト株式会社", market="Prime", sector="Technology"),
        models.Company(symbol="5678", name="サンプル商事", market="Standard", sector="Trading"),
        models.Company(symbol="9999", name="テストサービス", market="Growth", sector="Service"),
        models.Company(symbol="1111", name="Sample Corp", market="Prime", sector="Finance"),
    ]
    db_session.add_all(companies)
    db_session.commit()
    return companies


class TestGetAllCompanies:
    """get_all_companies メソッドのテスト。"""

    def test_get_all_companies_without_limit(self, company_filter_service, test_companies):
        """制限なしで全企業を取得。"""
        result = company_filter_service.get_all_companies(limit=None)

        assert len(result) == 4
        assert all("symbol" in company for company in result)
        assert all("name" in company for company in result)

    def test_get_all_companies_with_limit(self, company_filter_service, test_companies):
        """上限件数を指定して企業を取得。"""
        result = company_filter_service.get_all_companies(limit=2)

        assert len(result) == 2

    def test_get_all_companies_returns_dict(self, company_filter_service, test_companies):
        """返り値が辞書のリストであることを確認。"""
        result = company_filter_service.get_all_companies(limit=1)

        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        assert "symbol" in result[0]
        assert "name" in result[0]
        assert "market" in result[0]
        assert "sector" in result[0]

    def test_get_all_companies_empty_database(self, company_filter_service):
        """データベースが空の場合。"""
        result = company_filter_service.get_all_companies(limit=None)

        assert result == []

    def test_get_all_companies_limit_zero(self, company_filter_service, test_companies):
        """上限が0の場合は全件を返す（limitが適用されない）。"""
        result = company_filter_service.get_all_companies(limit=0)

        assert len(result) == 4  # 全件が返される

    def test_get_all_companies_limit_exceeds_total(self, company_filter_service, test_companies):
        """上限が総数を超える場合は全件を返す。"""
        result = company_filter_service.get_all_companies(limit=100)

        assert len(result) == 4  # 実際の企業数
