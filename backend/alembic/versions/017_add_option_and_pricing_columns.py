"""Add Option 2/3 and pricing columns to products table

Revision ID: 017
Revises: 016
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Option 2/3 name/value and pricing columns."""
    op.add_column('products', sa.Column('option_2_name', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('option_2_value', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('option_3_name', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('option_3_value', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('wholesale_price_usd', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('retail_price_usd', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove Option 2/3 and pricing columns."""
    op.drop_column('products', 'retail_price_usd')
    op.drop_column('products', 'wholesale_price_usd')
    op.drop_column('products', 'option_3_value')
    op.drop_column('products', 'option_3_name')
    op.drop_column('products', 'option_2_value')
    op.drop_column('products', 'option_2_name')
