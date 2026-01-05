"""銘柄コード（シンボル）に関するユーティリティ関数"""


def format_symbol(symbol: str) -> str:
    """
    日本株のシンボルをyfinance形式に変換

    Args:
        symbol: 銘柄コード（例: 7203）

    Returns:
        yfinance形式のシンボル（例: 7203.T）

    Examples:
        >>> format_symbol("7203")
        '7203.T'
        >>> format_symbol("7203.T")
        '7203.T'
    """
    if not symbol.endswith(".T"):
        return f"{symbol}.T"
    return symbol
