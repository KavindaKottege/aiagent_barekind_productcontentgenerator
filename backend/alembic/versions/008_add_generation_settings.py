"""Add generation settings to app_settings.

Revision ID: 008
Revises: 007
Create Date: 2026-01-23
"""

from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add generation settings columns
    op.add_column(
        "app_settings",
        sa.Column("ai_model", sa.String(50), nullable=False, server_default="gpt-5.2"),
    )
    op.add_column(
        "app_settings",
        sa.Column("ai_temperature", sa.Numeric(3, 2), nullable=False, server_default="0.7"),
    )
    op.add_column(
        "app_settings",
        sa.Column("generation_soft_cap", sa.Numeric(10, 2), nullable=False, server_default="500.00"),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "generation_soft_cap")
    op.drop_column("app_settings", "ai_temperature")
    op.drop_column("app_settings", "ai_model")
