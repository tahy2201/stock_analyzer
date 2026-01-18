"""AI株価分析API

銘柄のAI分析機能を提供するエンドポイント群
"""

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.api.schemas.ai_analysis import AnalysisListResponse, AnalysisResponse
from app.config.settings import AI_ANALYSIS_TIMEOUT_SECONDS
from app.database.database_manager import DatabaseManager
from app.database.models import AIStockAnalysis, User
from app.database.session import SessionLocal
from app.services.ai_stock_analysis_service import AIStockAnalysisService


def run_analysis_in_background(
    ai_service: AIStockAnalysisService,
    symbol: str,
    analysis_id: int,
    timeout_seconds: int,
) -> None:
    """バックグラウンドでAI分析を実行する同期ラッパー

    Args:
        ai_service: AI分析サービス
        symbol: 銘柄コード
        analysis_id: 分析ID
        timeout_seconds: タイムアウト秒数
    """
    asyncio.run(
        ai_service.analyze_stock_async(symbol, analysis_id, timeout_seconds)
    )

router = APIRouter()


def to_analysis_response(analysis: AIStockAnalysis) -> AnalysisResponse:
    """AIStockAnalysisモデルをAnalysisResponseに変換する

    Args:
        analysis: AIStockAnalysisモデル

    Returns:
        AnalysisResponse
    """
    return AnalysisResponse(
        id=analysis.id,
        symbol=analysis.symbol,
        status=analysis.status,
        analysis_text=analysis.analysis_text,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
    )


def get_db_manager() -> DatabaseManager:
    """データベースマネージャーを取得

    Returns:
        DatabaseManager インスタンス
    """
    return DatabaseManager()


def get_ai_service(db_manager: DatabaseManager = Depends(get_db_manager)) -> AIStockAnalysisService:
    """AI分析サービスを取得

    Args:
        db_manager: データベースマネージャー

    Returns:
        AIStockAnalysisService インスタンス
    """
    return AIStockAnalysisService(db_manager)


@router.post("/{symbol}", response_model=AnalysisResponse)
async def start_analysis(
    symbol: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    ai_service: AIStockAnalysisService = Depends(get_ai_service),
) -> AnalysisResponse:
    """銘柄のAI分析を開始する

    Args:
        symbol: 銘柄コード
        background_tasks: バックグラウンドタスク
        current_user: 現在のユーザー
        ai_service: AI分析サービス

    Returns:
        分析レスポンス（status: pending）

    Raises:
        HTTPException: 銘柄が見つからない場合
    """
    # 分析レコードを作成して取得（セッションを1つに統合）
    with SessionLocal() as session:
        try:
            analysis_id = ai_service.create_analysis_record(session, symbol, current_user.id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        # 作成した分析レコードを取得
        analysis = ai_service.get_analysis_by_id(session, analysis_id)
        if not analysis:
            raise HTTPException(status_code=500, detail="分析レコードの作成に失敗しました")
        response = to_analysis_response(analysis)

    # バックグラウンドで分析を実行
    background_tasks.add_task(
        run_analysis_in_background,
        ai_service,
        symbol,
        analysis_id,
        AI_ANALYSIS_TIMEOUT_SECONDS,
    )

    return response


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    ai_service: AIStockAnalysisService = Depends(get_ai_service),
) -> AnalysisResponse:
    """分析結果を取得する

    Args:
        analysis_id: 分析ID
        current_user: 現在のユーザー
        ai_service: AI分析サービス

    Returns:
        分析レスポンス

    Raises:
        HTTPException: 分析が見つからない、または権限がない場合
    """
    with SessionLocal() as session:
        analysis = ai_service.get_analysis_by_id(session, analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="分析結果が見つかりません")

        if analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="この分析結果にアクセスする権限がありません")

        return to_analysis_response(analysis)


@router.get("/history/{symbol}", response_model=AnalysisListResponse)
def get_analysis_history(
    symbol: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    ai_service: AIStockAnalysisService = Depends(get_ai_service),
) -> AnalysisListResponse:
    """銘柄の分析履歴を取得する

    Args:
        symbol: 銘柄コード
        limit: 取得件数（デフォルト: 10件）
        current_user: 現在のユーザー
        ai_service: AI分析サービス

    Returns:
        分析履歴リスト
    """
    with SessionLocal() as session:
        analyses = ai_service.get_user_analyses(session, current_user.id, symbol, limit)
        return AnalysisListResponse(
            analyses=[to_analysis_response(a) for a in analyses],
            total=len(analyses),
        )
