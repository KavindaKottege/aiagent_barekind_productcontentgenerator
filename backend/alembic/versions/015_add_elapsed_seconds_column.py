"""Add elapsed_seconds column to generation_jobs

Revision ID: 015
Revises: 014
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '015'
down_revision: Union[str, None] = '014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add elapsed_seconds column for cumulative running time."""
    op.add_column('generation_jobs', sa.Column('elapsed_seconds', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove elapsed_seconds column."""
    op.drop_column('generation_jobs', 'elapsed_seconds')
