"""Add soft_cap_threshold column to generation_jobs table

Revision ID: 018
Revises: 017
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft_cap_threshold column for tracking next soft cap trigger point."""
    op.add_column('generation_jobs',
        sa.Column('soft_cap_threshold', sa.Numeric(10, 4), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove soft_cap_threshold column."""
    op.drop_column('generation_jobs', 'soft_cap_threshold')
