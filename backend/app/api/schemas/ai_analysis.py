"""AI分析APIスキーマ

AI株価分析のリクエスト・レスポンスモデルを定義する。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    """分析レスポンスモデル"""

    id: int
    symbol: str
    status: str
    analysis_text: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AnalysisListResponse(BaseModel):
    """分析履歴リストレスポンスモデル"""

    analyses: list[AnalysisResponse]
    total: int
