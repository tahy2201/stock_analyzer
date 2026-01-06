"""数値処理に関するユーティリティ関数"""

import math
from typing import Optional

import pandas as pd


def is_valid_number(value: Optional[float]) -> bool:
    """
    数値が有効かチェック

    Args:
        value: チェック対象の値

    Returns:
        有効な数値の場合True
    """
    if value is None:
        return False

    if isinstance(value, float):
        return not (math.isnan(value) or math.isinf(value))

    # pandas NAType対応
    if pd.isna(value):
        return False

    return True


def safe_float(value: Optional[float], default: float = 0.0) -> float:
    """
    安全にfloat値を取得

    Args:
        value: 変換対象の値
        default: 無効な場合のデフォルト値

    Returns:
        有効な場合はfloat値、無効な場合はdefault
    """

    if value is not None and is_valid_number(value):
        # is_valid_number にもNoneチェックが入っているが、Pylanceチェックが通らないため
        # あえてNoneチェックしている。
        return float(value)
    else:
        return default
