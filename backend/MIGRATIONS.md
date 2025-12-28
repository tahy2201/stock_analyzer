# データベースマイグレーション運用ガイド

## 概要

Stock AnalyzerプロジェクトではAlembicを使用してデータベースマイグレーションを管理しています。

## 前提知識

- **Alembic**: SQLAlchemyベースのデータベースマイグレーションツール
- **マイグレーション**: データベーススキーマの変更を管理・適用する仕組み

## 基本コマンド

### マイグレーションの実行

最新のマイグレーションを適用する:
```bash
uv run python -m alembic upgrade head
```

### マイグレーションの作成

スキーマを変更した後、新しいマイグレーションスクリプトを生成する:
```bash
uv run python -m alembic revision --autogenerate -m "変更内容の説明"
```

### マイグレーション履歴の確認

現在のマイグレーション状態を確認:
```bash
uv run python -m alembic current
```

マイグレーション履歴を表示:
```bash
uv run python -m alembic history --verbose
```

### ロールバック

1つ前のバージョンに戻す:
```bash
uv run python -m alembic downgrade -1
```

特定のリビジョンに戻す:
```bash
uv run python -m alembic downgrade <revision_id>
```

すべてのマイグレーションを取り消す:
```bash
uv run python -m alembic downgrade base
```

## スキーマ変更の手順

### 1. モデルの変更

`backend/shared/database/models_orm.py` でSQLAlchemyモデルを変更します。

例: 新しいカラムを追加
```python
class Company(Base):
    __tablename__ = "companies"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # 新しいカラムを追加
    industry_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
```

### 2. マイグレーションスクリプトの生成

```bash
uv run python -m alembic revision --autogenerate -m "Add industry_code to companies table"
```

### 3. 生成されたスクリプトの確認

`backend/alembic/versions/` に新しいマイグレーションファイルが生成されます。
必ず内容を確認し、必要に応じて手動で調整してください。

### 4. マイグレーションの適用

開発環境でテスト:
```bash
uv run python -m alembic upgrade head
```

### 5. コードのコミット

マイグレーションスクリプトとモデルの変更をコミットします:
```bash
git add backend/shared/database/models_orm.py
git add backend/alembic/versions/
git commit -m "feat: Add industry_code column to companies table"
```

## Docker環境でのマイグレーション

### 開発環境（ローカル）

Docker起動時に自動的にマイグレーションが実行されます。

`backend/docker-entrypoint.sh` で以下が実行されます:
```bash
python -m alembic upgrade head
```

### 本番環境（Raspberry Pi）でのマイグレーション

本番環境でのデプロイ時は、以下の手順でマイグレーションを適用します。

#### 1. デプロイ前の確認

まず、新しいバージョンに含まれるマイグレーションを確認:
```bash
cd /path/to/stock_analyzer
git fetch --tags
git show v0.2.1:backend/alembic/versions/
```

#### 2. データベースのバックアップ（必須）

デプロイ前に必ずバックアップを取得:
```bash
# コンテナが起動している状態で実行
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  cp /app/data/stock_data.db /app/data/stock_data.db.backup.$(date +%Y%m%d_%H%M%S)

# バックアップをホストにコピー
docker compose -f docker-compose.yml -f docker-compose.prod.yml cp \
  backend:/app/data/stock_data.db.backup.$(date +%Y%m%d_%H%M%S) \
  ./backup/
```

#### 3. デプロイ実行

deploy.shスクリプトを実行:
```bash
./deploy.sh v0.2.1
```

デプロイスクリプトがコンテナを再起動すると、`docker-entrypoint.sh` が自動的に `alembic upgrade head` を実行します。

#### 4. マイグレーション適用の確認

コンテナ起動後、マイグレーションが正しく適用されたか確認:
```bash
# 現在のマイグレーションバージョンを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  python -m alembic current

# マイグレーション履歴を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  python -m alembic history --verbose
```

#### 5. アプリケーション動作確認

APIが正常に動作しているか確認:
```bash
# ヘルスチェック
curl http://localhost:8000/health

# ログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

#### マイグレーション失敗時のロールバック手順

マイグレーションが失敗した場合:

1. コンテナを停止:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

2. バックアップからDBを復元:
```bash
cp ./backup/stock_data.db.backup.YYYYMMDD_HHMMSS data/stock_data.db
```

3. 前のバージョンにロールバック:
```bash
git checkout v0.2.0  # 前のバージョンのタグ
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

4. 問題を調査してから再デプロイ

## トラブルシューティング

### マイグレーションが失敗する場合

1. データベースファイルをバックアップ:
```bash
cp data/stock_data.db data/stock_data.db.backup
```

2. 現在のマイグレーション状態を確認:
```bash
uv run python -m alembic current
```

3. 必要に応じてロールバック:
```bash
uv run python -m alembic downgrade -1
```

### autogenerateが変更を検出しない場合

手動でマイグレーションスクリプトを作成:
```bash
uv run python -m alembic revision -m "Manual migration description"
```

生成されたファイルを編集して、`upgrade()` と `downgrade()` 関数を実装してください。

### マイグレーションとモデルの不整合

データベースの状態をリセットして再構築:
```bash
# 既存DBをバックアップ
cp data/stock_data.db data/stock_data.db.backup

# DBを削除
rm data/stock_data.db

# マイグレーションを再実行
uv run python -m alembic upgrade head
```

## ベストプラクティス

1. **マイグレーションは小さく保つ**: 1つのマイグレーションで1つの変更を行う
2. **本番環境適用前にテスト**: 必ず開発環境でテストしてから本番環境に適用
3. **ロールバック可能に**: `downgrade()` 関数を正しく実装
4. **バックアップを取る**: 本番環境でのマイグレーション前に必ずバックアップ
5. **マイグレーションファイルの確認**: autogenerate後は必ず生成されたファイルを確認

## 参考資料

- [Alembic公式ドキュメント](https://alembic.sqlalchemy.org/)
- [SQLAlchemy公式ドキュメント](https://www.sqlalchemy.org/)
