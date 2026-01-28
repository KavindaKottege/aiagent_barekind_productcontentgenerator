"""Add option_type column to products table

Revision ID: 011
Revises: 010
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add option_type column to products."""
    op.add_column('products', sa.Column('option_type', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove option_type column."""
    op.drop_column('products', 'option_type')
