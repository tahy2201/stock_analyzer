# Stock Analyzer / Codex 作業ルール

## 目的
このリポジトリでのコード変更を安全かつ一貫性をもって行うためのガイドラインです。`.claude/CLAUDE.md` の内容をCodex向けに整理し、コミット運用ルールを追加しています。

## 配置・命名
- stock_analyzer直下にPythonファイルを置かないこと。
- バッチ関連は必ず `backend/batch/` に配置し、用途が明確なファイル名にすること（`run_batch.py` のような汎用名は禁止）。

## 実行・開発ルール
- 実行は uv 経由を推奨。例: `uv run python batch/stock_data_updater.py --markets prime`
- インポートは backend 内で相対パスを使用し、`from backend.` プレフィックスは禁止。
- FastAPI の依存関数は `api/dependencies/` に集約し、DB依存は `DBSession` エイリアスで記述する。
- B008（Dependsのデフォルト引数警告）はルーター/依存ファイルを per-file ignore で扱い、行ごとの `# noqa` は不要。
- 環境変数はむやみに増やさない。追加が必要な場合は事前に相談する。

## 品質チェック（最重要）
1. Pyright / mypy / ruff をすべて実行し、エラーゼロであること。
2. インポートパスとファイル配置が適切か確認すること。

## テスト
- 単体テスト実行例: `uv run --group dev pytest`
- カバレッジ付き: `uv run --group dev pytest --cov=api --cov=shared --cov=services`

## コミット運用
- **コミット前に必ず変更内容をユーザーへ報告し、明示的な承認を得ること。**
- 一時ファイル（例: `.coverage`）や生成物はコミットしないこと。
- 依存追加や設定変更は意味の分かる単位でコミットを分ける。
- 新たな指摘・運用ルールは都度このファイルに反映し、章立てに統合する（後でまとめ直す手戻りを防ぐ）。

## チェックリスト（コミット前）
- Pyright/mypy/ruff 全てエラーゼロ
- テスト実行（必要ならカバレッジ）
- ファイル配置・命名ルール遵守
- ユーザー承認取得済み

## リスク対応
- 破壊的操作（例: 既存DBテーブルのDROP）は必ずバックアップを取得し、事前にユーザー合意を得る。
