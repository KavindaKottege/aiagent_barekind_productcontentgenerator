"""Add cached tokens and cost breakdown columns to generation_jobs

Revision ID: 014
Revises: 013
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cached tokens and cost breakdown columns."""
    op.add_column('generation_jobs', sa.Column('total_cached_input_tokens', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('generation_jobs', sa.Column('total_input_cost', sa.Numeric(10, 6), nullable=False, server_default='0'))
    op.add_column('generation_jobs', sa.Column('total_cached_input_cost', sa.Numeric(10, 6), nullable=False, server_default='0'))
    op.add_column('generation_jobs', sa.Column('total_output_cost', sa.Numeric(10, 6), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove cached tokens and cost breakdown columns."""
    op.drop_column('generation_jobs', 'total_output_cost')
    op.drop_column('generation_jobs', 'total_cached_input_cost')
    op.drop_column('generation_jobs', 'total_input_cost')
    op.drop_column('generation_jobs', 'total_cached_input_tokens')
