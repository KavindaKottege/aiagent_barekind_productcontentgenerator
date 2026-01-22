"""Create generation_jobs and generation_audits tables.

Revision ID: 007
Revises: 006
Create Date: 2026-01-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create generation_jobs table
    op.create_table(
        'generation_jobs',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID, sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('total_count', sa.Integer, nullable=False, default=0),
        sa.Column('completed_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('projected_cost', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for generation_jobs
    op.create_index('ix_generation_jobs_client_id', 'generation_jobs', ['client_id'])
    op.create_index('ix_generation_jobs_user_id', 'generation_jobs', ['user_id'])
    op.create_index('ix_generation_jobs_status', 'generation_jobs', ['status'])

    # Create generation_audits table
    op.create_table(
        'generation_audits',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', UUID, sa.ForeignKey('generation_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_group_id', UUID, sa.ForeignKey('product_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_version', sa.String(100), nullable=False),
        sa.Column('temperature', sa.Numeric(3, 2), nullable=False),
        sa.Column('prompt_used', sa.Text, nullable=False),
        sa.Column('generated_title', sa.String(255), nullable=True),
        sa.Column('generated_description', sa.Text, nullable=True),
        sa.Column('input_tokens', sa.Integer, nullable=False, default=0),
        sa.Column('output_tokens', sa.Integer, nullable=False, default=0),
        sa.Column('cost', sa.Numeric(10, 6), nullable=False, default=0),
        sa.Column('title_length', sa.Integer, nullable=True),
        sa.Column('description_length', sa.Integer, nullable=True),
        sa.Column('attempt_number', sa.Integer, nullable=False, default=1),
        sa.Column('success', sa.Boolean, nullable=False, default=False),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for generation_audits
    op.create_index('ix_generation_audits_job_id', 'generation_audits', ['job_id'])
    op.create_index('ix_generation_audits_product_group_id', 'generation_audits', ['product_group_id'])


def downgrade() -> None:
    # Drop generation_audits table (cascade will handle foreign keys)
    op.drop_index('ix_generation_audits_product_group_id', 'generation_audits')
    op.drop_index('ix_generation_audits_job_id', 'generation_audits')
    op.drop_table('generation_audits')

    # Drop generation_jobs table
    op.drop_index('ix_generation_jobs_status', 'generation_jobs')
    op.drop_index('ix_generation_jobs_user_id', 'generation_jobs')
    op.drop_index('ix_generation_jobs_client_id', 'generation_jobs')
    op.drop_table('generation_jobs')
