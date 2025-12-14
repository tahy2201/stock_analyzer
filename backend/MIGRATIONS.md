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

Docker起動時に自動的にマイグレーションが実行されます。

`backend/docker-entrypoint.sh` で以下が実行されます:
```bash
python -m alembic upgrade head
```

## トラブルシューティング

### マイグレーションが失敗する場合

1. データベースファイルをバックアップ:
```bash
cp backend/data/stock_analyzer.db backend/data/stock_analyzer.db.backup
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
cp backend/data/stock_analyzer.db backend/data/stock_analyzer.db.backup

# DBを削除
rm backend/data/stock_analyzer.db

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
