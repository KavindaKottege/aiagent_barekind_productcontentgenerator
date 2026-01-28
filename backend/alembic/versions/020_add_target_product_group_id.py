"""Add target_product_group_id column to generation_jobs table

Revision ID: 020
Revises: 019
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '020'
down_revision: Union[str, None] = '019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add target_product_group_id column for single-product generation jobs."""
    op.add_column('generation_jobs',
        sa.Column('target_product_group_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_generation_jobs_target_product_group',
        'generation_jobs', 'product_groups',
        ['target_product_group_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(
        'ix_generation_jobs_target_product_group_id',
        'generation_jobs', ['target_product_group_id']
    )


def downgrade() -> None:
    """Remove target_product_group_id column."""
    op.drop_index('ix_generation_jobs_target_product_group_id', table_name='generation_jobs')
    op.drop_constraint('fk_generation_jobs_target_product_group', 'generation_jobs', type_='foreignkey')
    op.drop_column('generation_jobs', 'target_product_group_id')
