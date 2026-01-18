"""Claude APIサービス

Anthropic Claude APIとの通信を担当するサービス。
"""

from anthropic import Anthropic
from anthropic.types import Message, TextBlock

from app.config.settings import ANTHROPIC_API_KEY


class ClaudeService:
    """Claude APIサービスクラス"""

    def __init__(self) -> None:
        """サービスの初期化"""
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    def is_available(self) -> bool:
        """APIが利用可能かどうかを返す

        Returns:
            APIキーが設定されていればTrue
        """
        return self.client is not None

    def send_message(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2000,
    ) -> Message:
        """Claudeにメッセージを送信する

        Args:
            prompt: プロンプト
            model: 使用するモデル
            max_tokens: 最大トークン数

        Returns:
            APIレスポンス

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        if not self.client:
            raise ValueError("Anthropic APIキーが設定されていません")

        return self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

    def extract_text_from_response(self, response: Message) -> str:
        """レスポンスからテキストを抽出する

        Args:
            response: APIレスポンス

        Returns:
            抽出されたテキスト（取得できない場合はデフォルトメッセージ）
        """
        if response.content and len(response.content) > 0:
            first_block = response.content[0]
            if isinstance(first_block, TextBlock):
                return first_block.text
        return "レスポンスからテキストを取得できませんでした"
