"""Add ai_suggested_title and ai_suggested_description columns to product_groups

Revision ID: 019
Revises: 018
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '019'
down_revision: Union[str, None] = '018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AI suggested correction columns."""
    op.add_column('product_groups', sa.Column('ai_suggested_title', sa.Text(), nullable=True))
    op.add_column('product_groups', sa.Column('ai_suggested_description', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove AI suggested correction columns."""
    op.drop_column('product_groups', 'ai_suggested_description')
    op.drop_column('product_groups', 'ai_suggested_title')
