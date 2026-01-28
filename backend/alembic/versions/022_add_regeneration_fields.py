"""Add regeneration tracking fields to product_groups.

Revision ID: 022_add_regeneration_fields
Revises: 021_add_current_task_tracking
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rejection reasons - JSONB array of predefined reason strings
    op.add_column(
        "product_groups",
        sa.Column("rejection_reasons", JSONB, nullable=True, server_default="[]"),
    )

    # Regeneration count - tracks how many times content was regenerated
    op.add_column(
        "product_groups",
        sa.Column(
            "regeneration_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Index on regeneration_count for filtering products needing regeneration
    op.create_index(
        "ix_product_groups_regeneration_count",
        "product_groups",
        ["regeneration_count"],
    )


def downgrade() -> None:
    op.drop_index("ix_product_groups_regeneration_count", table_name="product_groups")
    op.drop_column("product_groups", "regeneration_count")
    op.drop_column("product_groups", "rejection_reasons")
