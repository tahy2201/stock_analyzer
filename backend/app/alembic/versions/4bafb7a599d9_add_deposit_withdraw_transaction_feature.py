"""入金・出金トランザクション機能を追加

Revision ID: 4bafb7a599d9
Revises: 0793f075e201
Create Date: 2026-01-02 14:18:41.486321

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4bafb7a599d9"
down_revision: Union[str, Sequence[str], None] = "0793f075e201"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLiteではカラム変更が制限されるため、テーブル再作成で対応
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.alter_column("symbol", existing_type=sa.VARCHAR(length=10), nullable=True)
        batch_op.alter_column(
            "transaction_type",
            existing_type=sa.VARCHAR(length=4),
            type_=sa.Enum(
                "buy", "sell", "deposit", "withdrawal", name="transaction_type", native_enum=False
            ),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    # SQLiteではカラム変更が制限されるため、テーブル再作成で対応
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.alter_column(
            "transaction_type",
            existing_type=sa.Enum(
                "buy", "sell", "deposit", "withdrawal", name="transaction_type", native_enum=False
            ),
            type_=sa.VARCHAR(length=4),
            existing_nullable=False,
        )
        batch_op.alter_column("symbol", existing_type=sa.VARCHAR(length=10), nullable=False)
