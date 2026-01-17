"""AI株価分析結果テーブルを追加

Revision ID: d4dae558d760
Revises: 4bafb7a599d9
Create Date: 2026-01-17 00:04:38.580721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4dae558d760'
down_revision: Union[str, Sequence[str], None] = '4bafb7a599d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ai_stock_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', name='ai_analysis_status', native_enum=False, validate_strings=True), nullable=False),
        sa.Column('analysis_text', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['symbol'], ['companies.symbol'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_analyses_status', 'ai_stock_analyses', ['status'], unique=False)
    op.create_index('idx_ai_analyses_user_symbol', 'ai_stock_analyses', ['user_id', 'symbol'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_ai_analyses_user_symbol', table_name='ai_stock_analyses')
    op.drop_index('idx_ai_analyses_status', table_name='ai_stock_analyses')
    op.drop_table('ai_stock_analyses')
