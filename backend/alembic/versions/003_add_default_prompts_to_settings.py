"""Add default prompt columns to app_settings

Revision ID: 003
Revises: 002
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default prompt columns to app_settings table."""
    op.add_column("app_settings", sa.Column("default_system_prompt", sa.Text(), nullable=True))
    op.add_column("app_settings", sa.Column("default_task1_prompt", sa.Text(), nullable=True))
    op.add_column("app_settings", sa.Column("default_task2_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove default prompt columns from app_settings table."""
    op.drop_column("app_settings", "default_task2_prompt")
    op.drop_column("app_settings", "default_task1_prompt")
    op.drop_column("app_settings", "default_system_prompt")
