"""数値処理ユーティリティ関数のテスト"""

import math

import pandas as pd

from app.utils.numeric import is_valid_number, safe_float


class TestIsValidNumber:
    """is_valid_number関数のテスト"""

    def test_is_valid_number_with_valid_float(self):
        """有効なfloat値のテスト"""
        assert is_valid_number(1.5) is True
        assert is_valid_number(0.0) is True
        assert is_valid_number(-10.5) is True

    def test_is_valid_number_with_none(self):
        """Noneのテスト"""
        assert is_valid_number(None) is False

    def test_is_valid_number_with_nan(self):
        """NaNのテスト"""
        assert is_valid_number(float("nan")) is False
        assert is_valid_number(math.nan) is False

    def test_is_valid_number_with_inf(self):
        """Infinityのテスト"""
        assert is_valid_number(float("inf")) is False
        assert is_valid_number(float("-inf")) is False
        assert is_valid_number(math.inf) is False

    def test_is_valid_number_with_pandas_na(self):
        """pandas NATypeのテスト"""
        assert is_valid_number(pd.NA) is False


class TestSafeFloat:
    """safe_float関数のテスト"""

    def test_safe_float_with_valid_value(self):
        """有効な値のテスト"""
        assert safe_float(1.5) == 1.5
        assert safe_float(0.0) == 0.0
        assert safe_float(-10.5) == -10.5

    def test_safe_float_with_none(self):
        """Noneの場合のデフォルト値テスト"""
        assert safe_float(None) == 0.0
        assert safe_float(None, default=5.0) == 5.0

    def test_safe_float_with_nan(self):
        """NaNの場合のデフォルト値テスト"""
        assert safe_float(float("nan")) == 0.0
        assert safe_float(math.nan, default=10.0) == 10.0

    def test_safe_float_with_custom_default(self):
        """カスタムデフォルト値のテスト"""
        assert safe_float(None, default=99.9) == 99.9
        assert safe_float(float("inf"), default=100.0) == 100.0
        assert safe_float(pd.NA, default=-1.0) == -1.0
