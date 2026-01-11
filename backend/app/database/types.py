"""データベース関連の型定義"""

from datetime import datetime
from typing import Optional

# 銘柄ごとの最新日付マップ
SymbolDateMap = dict[str, Optional[datetime]]

# 企業情報辞書
CompanyDict = dict[str, str | int | float | bool | None]

# 分析結果辞書（オプショナル）
AnalysisResultMap = dict[str, Optional[dict]]
