"""Add first_row_index to product_groups

Revision ID: 010
Revises: 009
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add first_row_index column to product_groups."""
    op.add_column(
        'product_groups',
        sa.Column('first_row_index', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    """Remove first_row_index column."""
    op.drop_column('product_groups', 'first_row_index')
