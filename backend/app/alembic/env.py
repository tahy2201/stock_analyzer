from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# DATABASE_PATHを取得するためにsettingsをインポート
from app.config.settings import DATABASE_PATH

# 自動生成サポートのため、全てのモデルをインポート
from app.database.models import Base

# Alembic Configオブジェクト（.iniファイルの値にアクセス可能）
config = context.config

# settingsのDATABASE_PATHでsqlalchemy.urlを上書き
config.set_main_option("sqlalchemy.url", f"sqlite:///{DATABASE_PATH}")

# Python loggingのための設定ファイルを解釈
# この行で基本的にロガーをセットアップ
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 自動生成サポートのため、モデルのMetaDataオブジェクトを追加
target_metadata = Base.metadata


def run_migrations() -> None:
    """データベースマイグレーションを実行

    Engineを作成し、データベースに接続してマイグレーションを適用します。

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
