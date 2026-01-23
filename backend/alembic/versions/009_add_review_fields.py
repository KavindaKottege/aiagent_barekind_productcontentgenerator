"""Add review fields to product_groups and create review_jobs table.

Revision ID: 009
Revises: 008
Create Date: 2026-01-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add review fields to product_groups table
    op.add_column('product_groups', sa.Column('edited_title', sa.String(255), nullable=True))
    op.add_column('product_groups', sa.Column('edited_description', sa.Text, nullable=True))
    op.add_column('product_groups', sa.Column('review_status', sa.String(50), nullable=True))
    op.add_column('product_groups', sa.Column('ai_review_status', sa.String(50), nullable=True))
    op.add_column('product_groups', sa.Column('ai_review_reason', sa.String(500), nullable=True))
    op.add_column('product_groups', sa.Column('ai_review_safety_flags', JSONB, nullable=True, server_default='[]'))
    op.add_column('product_groups', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('product_groups', sa.Column('ai_reviewed_at', sa.DateTime(timezone=True), nullable=True))

    # Create indexes for review status filtering
    op.create_index('ix_product_groups_review_status', 'product_groups', ['review_status'])
    op.create_index('ix_product_groups_ai_review_status', 'product_groups', ['ai_review_status'])

    # Create review_jobs table
    op.create_table(
        'review_jobs',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID, sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('total_count', sa.Integer, nullable=False, default=0),
        sa.Column('completed_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for review_jobs
    op.create_index('ix_review_jobs_client_id', 'review_jobs', ['client_id'])
    op.create_index('ix_review_jobs_user_id', 'review_jobs', ['user_id'])
    op.create_index('ix_review_jobs_status', 'review_jobs', ['status'])


def downgrade() -> None:
    # Drop review_jobs table
    op.drop_index('ix_review_jobs_status', 'review_jobs')
    op.drop_index('ix_review_jobs_user_id', 'review_jobs')
    op.drop_index('ix_review_jobs_client_id', 'review_jobs')
    op.drop_table('review_jobs')

    # Drop indexes from product_groups
    op.drop_index('ix_product_groups_ai_review_status', 'product_groups')
    op.drop_index('ix_product_groups_review_status', 'product_groups')

    # Drop review columns from product_groups
    op.drop_column('product_groups', 'ai_reviewed_at')
    op.drop_column('product_groups', 'reviewed_at')
    op.drop_column('product_groups', 'ai_review_safety_flags')
    op.drop_column('product_groups', 'ai_review_reason')
    op.drop_column('product_groups', 'ai_review_status')
    op.drop_column('product_groups', 'review_status')
    op.drop_column('product_groups', 'edited_description')
    op.drop_column('product_groups', 'edited_title')
