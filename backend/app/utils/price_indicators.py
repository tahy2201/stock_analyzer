import pandas as pd

from app.config.settings import MA_PERIOD
from app.utils.numeric import is_valid_number


def calculate_moving_average(prices: pd.Series, period: int = MA_PERIOD) -> pd.Series:
    """
    移動平均を計算
    """
    return prices.rolling(window=period, min_periods=period).mean()


def calculate_divergence_rate(current_price: float, ma_price: float) -> float:
    """
    移動平均からの乖離率を計算
    """
    if not is_valid_number(ma_price) or ma_price == 0:
        return 0.0

    divergence = ((current_price - ma_price) / ma_price) * 100
    return round(divergence, 2)


def calculate_volume_average(volumes: pd.Series, period: int = 20) -> pd.Series:
    """
    出来高の移動平均を計算
    """
    return volumes.rolling(window=period, min_periods=period).mean()


def calculate_price_change_percent(current_price: float, previous_price: float) -> float:
    """
    価格変化率を計算

    Args:
        current_price: 現在価格
        previous_price: 前回価格

    Returns:
        変化率（%）
    """
    if previous_price == 0 or pd.isna(previous_price):
        return 0.0

    return round(((current_price - previous_price) / previous_price) * 100, 2)
