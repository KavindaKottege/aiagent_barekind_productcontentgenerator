"""Add current task tracking columns for real-time UI updates.

Revision ID: 021_add_current_task_tracking
Revises: 020_add_target_product_group_id
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Current processing state
    op.add_column(
        "generation_jobs",
        sa.Column("current_product_name", sa.String(500), nullable=True),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("current_task", sa.String(50), nullable=True),
    )

    # Attempt tracking for current product (JSON arrays)
    op.add_column(
        "generation_jobs",
        sa.Column("task1_attempts", JSON, nullable=True),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("task2_attempts", JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generation_jobs", "task2_attempts")
    op.drop_column("generation_jobs", "task1_attempts")
    op.drop_column("generation_jobs", "current_task")
    op.drop_column("generation_jobs", "current_product_name")
