"""Add excel_column_order to clients table.

Revision ID: 023
Revises: 022
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("excel_column_order", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clients", "excel_column_order")
