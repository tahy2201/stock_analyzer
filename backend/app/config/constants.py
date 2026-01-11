"""共通定数定義"""

# 市場区分マッピング（英語名 → 日本語正式名称）
MARKET_NAME_MAPPING: dict[str, str] = {
    "prime": "プライム（内国株式）",
    "standard": "スタンダード（内国株式）",
    "growth": "グロース（内国株式）",
}

# テクニカル分析関連の定数
MA_WINDOW_SHORT = 25  # 短期移動平均ウィンドウ（日）
MA_WINDOW_LONG = 75  # 長期移動平均ウィンドウ（日）
TRADING_DAYS_PER_YEAR = 252  # 年間取引日数（ボラティリティ年率換算用）
VOLATILITY_WINDOW = 30  # ボラティリティ計算期間（日）
DIVERGENCE_THRESHOLD_STRONG = 5.0  # 強気/弱気判定の乖離率閾値（%）
VOLUME_MA_PERIOD = 20  # 出来高移動平均期間（日）

# セキュリティ関連の定数
TOKEN_LENGTH = 32  # トークン生成デフォルト長（バイト）
