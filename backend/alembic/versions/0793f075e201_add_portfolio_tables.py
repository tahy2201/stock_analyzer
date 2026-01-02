"""add_portfolio_tables

Revision ID: 0793f075e201
Revises: 2bc56d7af600
Create Date: 2025-12-30 11:35:12.121704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0793f075e201'
down_revision: Union[str, Sequence[str], None] = '2bc56d7af600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # portfolios テーブル作成
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('initial_capital', sa.DECIMAL(precision=15, scale=2), server_default='1000000.00', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_portfolios_user_id', 'portfolios', ['user_id'])

    # positions テーブル作成
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('average_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['symbol'], ['companies.symbol'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('portfolio_id', 'symbol', name='uq_positions_portfolio_symbol')
    )
    op.create_index('idx_positions_portfolio_id', 'positions', ['portfolio_id'])
    op.create_index('idx_positions_symbol', 'positions', ['symbol'])

    # transactions テーブル作成
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('transaction_type', sa.Enum('buy', 'sell', name='transaction_type', native_enum=False, validate_strings=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('profit_loss', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['symbol'], ['companies.symbol'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transactions_portfolio_id', 'transactions', ['portfolio_id'])
    op.create_index('idx_transactions_symbol', 'transactions', ['symbol'])
    op.create_index('idx_transactions_date', 'transactions', ['transaction_date'])
    op.create_index('idx_transactions_portfolio_date', 'transactions', ['portfolio_id', 'transaction_date'])


def downgrade() -> None:
    """Downgrade schema."""
    # テーブル削除（外部キー制約を持つテーブルから先に削除）
    op.drop_index('idx_transactions_portfolio_date', table_name='transactions')
    op.drop_index('idx_transactions_date', table_name='transactions')
    op.drop_index('idx_transactions_symbol', table_name='transactions')
    op.drop_index('idx_transactions_portfolio_id', table_name='transactions')
    op.drop_table('transactions')

    op.drop_index('idx_positions_symbol', table_name='positions')
    op.drop_index('idx_positions_portfolio_id', table_name='positions')
    op.drop_table('positions')

    op.drop_index('idx_portfolios_user_id', table_name='portfolios')
    op.drop_table('portfolios')
