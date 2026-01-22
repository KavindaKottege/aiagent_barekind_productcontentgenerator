"""Create clients table

Revision ID: 004
Revises: 003
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create clients table."""
    # Create clients table
    op.execute("""
        CREATE TABLE clients (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            brand_name VARCHAR(255) NOT NULL,
            story TEXT,
            tone VARCHAR(255),
            language VARCHAR(100),
            guidelines TEXT,
            system_prompt TEXT,
            task1_prompt TEXT,
            task2_prompt TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Create index on user_id for faster lookups
    op.execute("""
        CREATE INDEX ix_clients_user_id ON clients (user_id);
    """)


def downgrade() -> None:
    """Drop clients table."""
    op.drop_table('clients')
