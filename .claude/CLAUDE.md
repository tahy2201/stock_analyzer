# Stock Analyzer Project Rules

## ファイル配置ルール
- stock_analyzer直下にpythonファイルを置かないこと
- バッチ処理に必要なものはすべてbackend/batchフォルダに収めること
- 各ファイルは目的が明確に分かる名前を付けること

## バッチ実行ルール
- バッチファイルは用途別に明確な名前を付けること
- `run_batch.py`のような汎用的な名前は使用禁止
- 他のバッチファイルとの識別が困難になるため

## 推奨実行方法
- uvを使用してバッチを実行すること
- 例: `uv run python batch/stock_data_updater.py --markets prime`
- plain pythonではなくuvを使用する理由は依存関係管理のため

## コード品質ルール - **最重要**
- **修正を行った後は必ずPylance、mypy、ruffエラーチェックを実行すること**
- **Pylanceエラーが出た場合は必ず解消してからコミット/デプロイすること**
- **エラーが出た場合は必ず対応してからコミット/デプロイすること**
- **型チェックとlintingは必須**
- **Pylanceエラーは絶対に残してはいけない**

## インポートルール
- backendディレクトリ内では相対インポートを使用すること
- `from backend.` プレフィックスは使用禁止
- 例: `from shared.database.database_manager import DatabaseManager`

## 実行時チェック項目
1. ファイル名が目的を明確に表しているか
2. 適切なディレクトリに配置されているか
3. uvを使用した実行コマンドになっているか
4. **Pylanceエラーがないか（最重要）**
5. mypy、ruffエラーがないか
6. インポートパスが正しいか