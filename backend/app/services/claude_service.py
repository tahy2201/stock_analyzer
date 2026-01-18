"""Claude APIサービス

Anthropic Claude APIとの通信を担当するサービス。
"""

import logging

from anthropic import Anthropic, APIConnectionError, APIError, RateLimitError
from anthropic.types import Message, TextBlock

from app.config.settings import ANTHROPIC_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL

logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Claude API呼び出し時のエラー"""

    pass


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
        model: str = CLAUDE_MODEL,
        max_tokens: int = CLAUDE_MAX_TOKENS,
    ) -> Message:
        """Claudeにメッセージを送信する

        Args:
            prompt: プロンプト
            model: 使用するモデル
            max_tokens: 最大トークン数

        Returns:
            APIレスポンス

        Raises:
            ClaudeAPIError: API呼び出しに失敗した場合
        """
        if not self.client:
            logger.error("Anthropic APIキーが設定されていません")
            raise ClaudeAPIError("APIキーが設定されていません")

        logger.info("Claude APIにリクエストを送信します (model=%s, max_tokens=%d)", model, max_tokens)

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            logger.info(
                "Claude APIからレスポンスを受信しました (stop_reason=%s)",
                response.stop_reason,
            )
            return response

        except RateLimitError as e:
            logger.warning("Claude API: レート制限に達しました")
            raise ClaudeAPIError(
                "APIのレート制限に達しました。しばらく待ってから再試行してください"
            ) from e
        except APIConnectionError as e:
            logger.error("Claude API: 接続エラーが発生しました")
            raise ClaudeAPIError("APIへの接続に失敗しました") from e
        except APIError as e:
            logger.error("Claude API: エラーが発生しました: %s", str(e))
            raise ClaudeAPIError("API呼び出し中にエラーが発生しました") from e

    def extract_text_from_response(self, response: Message) -> str:
        """レスポンスからテキストを抽出する

        Args:
            response: APIレスポンス

        Returns:
            抽出されたテキスト

        Raises:
            ClaudeAPIError: レスポンスからテキストを抽出できない場合
        """
        if not response.content:
            logger.warning("Claude APIレスポンスにcontentがありません")
            raise ClaudeAPIError("APIレスポンスが空です")

        if len(response.content) == 0:
            logger.warning("Claude APIレスポンスのcontentが空です")
            raise ClaudeAPIError("APIレスポンスが空です")

        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            logger.warning(
                "Claude APIレスポンスの最初のブロックがTextBlockではありません (type=%s)",
                type(first_block).__name__,
            )
            raise ClaudeAPIError("APIレスポンスの形式が不正です")

        if not first_block.text:
            logger.warning("Claude APIレスポンスのテキストが空です")
            raise ClaudeAPIError("APIレスポンスのテキストが空です")

        return first_block.text
