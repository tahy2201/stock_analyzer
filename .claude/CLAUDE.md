# Stock Analyzer Project Rules

## ファイル配置ルール
- stock_analyzer直下にpythonファイルを置かないこと
- バッチ処理に必要なものはすべてbackend/app/batchフォルダに収めること
- 各ファイルは目的が明確に分かる名前を付けること

## バッチ実行ルール
- バッチファイルは用途別に明確な名前を付けること
- `run_batch.py`のような汎用的な名前は使用禁止
- 他のバッチファイルとの識別が困難になるため

## 推奨実行方法
- uvを使用してバッチを実行すること
- 例: `uv run python -m app.batch.stock_updater --markets prime`
- plain pythonではなくuvを使用する理由は依存関係管理のため

## コード品質ルール - **最重要**
- **修正を行った後は必ずPylance、mypy、ruffエラーチェックを実行すること**
- **Pylanceエラーが出た場合は必ず解消してからコミット/デプロイすること**
- **エラーが出た場合は必ず対応してからコミット/デプロイすること**
- **型チェックとlintingは必須**
- **Pylanceエラーは絶対に残してはいけない**

### バックエンド（Python）
- `uv run mypy <ファイルパス>` でmypy型チェックを実行
- `uv run ruff check <ファイルパス>` でruff lintingを実行

### フロントエンド（TypeScript）
- **必ず `npx tsc --noEmit --project tsconfig.app.json` でTypeScriptエラーを詳細確認すること**
- VSCodeの診断だけでなく、CLIでの確認も必須
- エラーが見つかった場合は必ず全て解消してからコミット
- **重要**: `tsconfig.json`ではなく`tsconfig.app.json`を指定すること（ルートのtsconfigはファイルを含まないため）
- 確認コマンド例:
  ```bash
  # プロジェクト全体のTypeScriptエラーをチェック（必ずtsconfig.app.jsonを指定）
  npx tsc --noEmit --project tsconfig.app.json

  # 特定のファイルを含むエラーを確認
  npx tsc --noEmit --project tsconfig.app.json 2>&1 | grep "ファイル名"
  ```

## ドキュメント文字列（docstring）ルール
- **docstringは日本語で記述すること**
- このプロジェクトは公開を想定していないため、チーム内での理解を優先する
- モジュール、クラス、関数、メソッドの先頭にdocstringを配置すること
- Google Style docstringフォーマットを使用すること
- 例:
  ```python
  def buy_stock(self, symbol: str, quantity: int):
      """銘柄を購入する。

      Args:
          symbol: 銘柄コード
          quantity: 購入株数

      Returns:
          取引記録
      """
  ```

## インポートルール
- backend/app/ディレクトリ内では絶対インポートを使用すること
- `from backend.` プレフィックスは使用禁止
- app/内のモジュールは`from app.`プレフィックスでインポート
- 例: `from app.database.database_manager import DatabaseManager`

## データベーススキーマルール
- **スキーマ確認は `backend/app/shared/database/models.py` を参照すること**
- 全テーブル定義とカラム情報はmodels.pyに集約されている
- マイグレーションファイルは `backend/app/alembic/versions/` に配置

## Git コミットルール - **最重要**
- **コミット前の手順を必ず守ること**
  1. **動作確認**: 修正内容が正しく動作することを確認
  2. **変更内容の提示**: `git diff` で変更内容を表示
  3. **説明**: 変更ファイルと変更内容を説明
  4. **承認待ち**: ユーザーの承認を得てからコミット
- **コミットメッセージは日本語で記述すること**
- コミット時は必ずフッターに以下を含めること:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
  ```

## 実行時チェック項目
1. ファイル名が目的を明確に表しているか
2. 適切なディレクトリに配置されているか
3. uvを使用した実行コマンドになっているか
4. **Pylanceエラーがないか（最重要）**
5. **バックエンド**: mypy、ruffエラーがないか
6. **フロントエンド**: `npx tsc --noEmit --project tsconfig.app.json` でTypeScriptエラーがないか（最重要）
7. インポートパスが正しいか
8. **コミットメッセージは日本語か**