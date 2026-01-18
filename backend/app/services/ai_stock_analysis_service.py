"""AI株価分析サービス

Claude APIを使用して銘柄の詳細分析を実行する。
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database_manager import DatabaseManager
from app.database.models import AIStockAnalysis, Company, StockPrice, TechnicalIndicator
from app.database.session import SessionLocal
from app.services.claude_service import ClaudeService


class AIStockAnalysisService:
    """AI株価分析サービスクラス"""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """サービスの初期化

        Args:
            db_manager: データベースマネージャー
        """
        self.db_manager = db_manager
        self.claude_service = ClaudeService()

    def get_stock_data_for_analysis(
        self, session: Session, symbol: str, days: int = 90
    ) -> dict[str, Any]:
        """分析用の株価データを取得する

        Args:
            session: データベースセッション
            symbol: 銘柄コード
            days: データ取得日数（デフォルト: 90日）

        Returns:
            株価データと企業情報を含む辞書
        """
        # 企業情報を取得
        company = session.scalar(select(Company).where(Company.symbol == symbol))
        if not company:
            raise ValueError(f"銘柄 {symbol} が見つかりません")

        # 過去90日間の株価データを取得
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        stock_prices = session.scalars(
            select(StockPrice)
            .where(StockPrice.symbol == symbol, StockPrice.date >= start_date)
            .order_by(StockPrice.date.desc())
        ).all()

        # 最新のテクニカル指標を取得
        latest_indicator = session.scalar(
            select(TechnicalIndicator)
            .where(TechnicalIndicator.symbol == symbol)
            .order_by(TechnicalIndicator.date.desc())
            .limit(1)
        )

        return {
            "company": company,
            "stock_prices": stock_prices,
            "latest_indicator": latest_indicator,
        }

    def build_analysis_prompt(self, data: dict[str, Any]) -> str:
        """分析用プロンプトを構築する

        Args:
            data: 株価データと企業情報

        Returns:
            構築されたプロンプト
        """
        company = data["company"]
        stock_prices = data["stock_prices"]
        latest_indicator = data["latest_indicator"]

        # 株価データの統計情報を計算
        if stock_prices:
            prices = [float(sp.close) for sp in stock_prices if sp.close is not None]
            current_price = prices[0] if prices else 0
            oldest_price = prices[-1] if prices else 0
            max_price = max(prices) if prices else 0
            min_price = min(prices) if prices else 0
            price_change_pct = (
                ((current_price - oldest_price) / oldest_price * 100) if oldest_price else 0
            )
        else:
            current_price = 0
            oldest_price = 0
            max_price = 0
            min_price = 0
            price_change_pct = 0

        # プロンプト構築
        prompt = f"""あなたは日本株の投資分析専門家です。以下の銘柄について、詳細な分析を行ってください。

【銘柄情報】
銘柄コード: {company.symbol}
銘柄名: {company.name or "不明"}
業種: {company.sector or "不明"}
市場区分: {company.market or "不明"}

【株価推移（過去90日間）】
現在価格: {current_price:,.0f}円
90日前価格: {oldest_price:,.0f}円
変動率: {price_change_pct:+.1f}%
期間最高値: {max_price:,.0f}円
期間最安値: {min_price:,.0f}円

【テクニカル指標】"""

        if latest_indicator:
            prompt += f"""
25日移動平均: {float(latest_indicator.ma_25):,.0f}円
乖離率: {float(latest_indicator.divergence_rate):+.1f}%
配当利回り: {float(latest_indicator.dividend_yield or 0):.2f}%"""
        else:
            prompt += "\nテクニカル指標データなし"

        prompt += """

【分析指示】
以下の形式で詳細な分析を提供してください：

## 株価動向分析（過去90日）

**価格推移:**
- 90日前、現在、最高値、最安値を明記
- 主要な変動要因を3つ挙げる

**テクニカル指標:**
- 移動平均からの乖離、配当利回りの評価
- 売られすぎ/買われすぎの判断

## 投資判断

**1ヶ月:** 買い推奨度 ★☆☆☆☆〜★★★★★（5段階評価）
短期的な見通しと根拠

**3ヶ月:** 買い推奨度 ★☆☆☆☆〜★★★★★（5段階評価）
中期的な見通しと根拠

**1年:** 買い推奨度 ★☆☆☆☆〜★★★★★（5段階評価）
長期的な見通しと根拠

**それ以上:** 買い推奨度 ★☆☆☆☆〜★★★★★（5段階評価）
超長期的な見通しと根拠

**総評:**
総合的な投資判断（2-3文）

注意: 株価の下落理由については、一般的な市場動向や業界トレンドに基づいて推測してください。
"""

        return prompt

    def _record_analysis_failure(self, analysis_id: int, error_message: str) -> None:
        """分析失敗をデータベースに記録する

        Args:
            analysis_id: 分析ID
            error_message: エラーメッセージ
        """
        with SessionLocal() as session:
            analysis = session.get(AIStockAnalysis, analysis_id)
            if analysis:
                analysis.status = "failed"
                analysis.error_message = error_message
                analysis.completed_at = datetime.now(timezone.utc)
                session.commit()

    async def analyze_stock_async(
        self, symbol: str, analysis_id: int, timeout_seconds: int = 60
    ) -> None:
        """株価をAI分析する（非同期）

        Args:
            symbol: 銘柄コード
            analysis_id: 分析ID
            timeout_seconds: タイムアウト秒数（デフォルト: 60秒）
        """
        try:
            await asyncio.wait_for(
                self._perform_analysis(symbol, analysis_id), timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            self._record_analysis_failure(analysis_id, "分析がタイムアウトしました（60秒）")
        except Exception as e:
            self._record_analysis_failure(analysis_id, f"分析中にエラーが発生しました: {e}")

    async def _perform_analysis(self, symbol: str, analysis_id: int) -> None:
        """分析を実行する内部メソッド

        Args:
            symbol: 銘柄コード
            analysis_id: 分析ID
        """
        # APIキーチェック
        if not self.claude_service.is_available():
            raise ValueError("Anthropic APIキーが設定されていません")

        # 株価データを取得
        with SessionLocal() as session:
            data = self.get_stock_data_for_analysis(session, symbol)

        # プロンプト構築
        prompt = self.build_analysis_prompt(data)

        # Claude APIに分析を依頼
        response = await asyncio.to_thread(self.claude_service.send_message, prompt)

        # 分析結果を取得
        analysis_text = self.claude_service.extract_text_from_response(response)

        # データベースに保存
        with SessionLocal() as session:
            analysis = session.get(AIStockAnalysis, analysis_id)
            if analysis:
                analysis.status = "completed"
                analysis.analysis_text = analysis_text
                analysis.completed_at = datetime.now(timezone.utc)
                session.commit()

    def create_analysis_record(self, session: Session, symbol: str, user_id: int) -> int:
        """分析レコードを作成する

        Args:
            session: データベースセッション
            symbol: 銘柄コード
            user_id: ユーザーID

        Returns:
            作成された分析レコードのID
        """
        analysis = AIStockAnalysis(
            symbol=symbol,
            user_id=user_id,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)
        return analysis.id

    def get_analysis_by_id(self, session: Session, analysis_id: int) -> Optional[AIStockAnalysis]:
        """分析結果をIDで取得する

        Args:
            session: データベースセッション
            analysis_id: 分析ID

        Returns:
            分析結果（存在しない場合はNone）
        """
        return session.get(AIStockAnalysis, analysis_id)

    def get_user_analyses(
        self, session: Session, user_id: int, symbol: Optional[str] = None, limit: int = 10
    ) -> list[AIStockAnalysis]:
        """ユーザーの分析履歴を取得する

        Args:
            session: データベースセッション
            user_id: ユーザーID
            symbol: 銘柄コード（オプション）
            limit: 取得件数（デフォルト: 10件）

        Returns:
            分析結果のリスト
        """
        query = select(AIStockAnalysis).where(AIStockAnalysis.user_id == user_id)

        if symbol:
            query = query.where(AIStockAnalysis.symbol == symbol)

        query = query.order_by(AIStockAnalysis.created_at.desc()).limit(limit)

        return list(session.scalars(query).all())
