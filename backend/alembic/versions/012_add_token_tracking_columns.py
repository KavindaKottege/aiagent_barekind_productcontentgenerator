"""Add token tracking columns to generation_jobs

Revision ID: 012
Revises: 011
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add token tracking columns."""
    op.add_column('generation_jobs', sa.Column('total_input_tokens', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('generation_jobs', sa.Column('total_output_tokens', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove token tracking columns."""
    op.drop_column('generation_jobs', 'total_output_tokens')
    op.drop_column('generation_jobs', 'total_input_tokens')
