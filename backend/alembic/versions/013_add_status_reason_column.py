"""Add status_reason column to generation_jobs

Revision ID: 013
Revises: 012
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status_reason column."""
    op.add_column('generation_jobs', sa.Column('status_reason', sa.String(500), nullable=True))


def downgrade() -> None:
    """Remove status_reason column."""
    op.drop_column('generation_jobs', 'status_reason')
