"""銘柄コード関連ユーティリティ関数のテスト"""

from app.utils.symbol import format_symbol


class TestFormatSymbol:
    """format_symbol関数のテスト"""

    def test_format_symbol_without_suffix(self):
        """サフィックスなしの銘柄コードのテスト"""
        assert format_symbol("7203") == "7203.T"
        assert format_symbol("6758") == "6758.T"
        assert format_symbol("9984") == "9984.T"

    def test_format_symbol_with_suffix(self):
        """既にサフィックス付きの銘柄コードのテスト"""
        assert format_symbol("7203.T") == "7203.T"
        assert format_symbol("6758.T") == "6758.T"
        assert format_symbol("9984.T") == "9984.T"

    def test_format_symbol_empty_string(self):
        """空文字列のエッジケーステスト"""
        assert format_symbol("") == ".T"
