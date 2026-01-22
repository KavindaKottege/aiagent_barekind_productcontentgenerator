"""create users table with RLS

Revision ID: 001
Revises:
Create Date: 2026-01-22 08:13:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table with Row-Level Security."""
    # Create users table
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            hashed_password TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Create unique index on email
    op.execute("""
        CREATE UNIQUE INDEX ix_users_email ON users (email);
    """)

    # Enable Row-Level Security
    op.execute("""
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    """)

    # Create RLS policy for user isolation
    # Users can only access their own data when app.current_user_id is set
    op.execute("""
        CREATE POLICY user_isolation_policy ON users
            FOR ALL
            USING (id::text = current_setting('app.current_user_id', true))
            WITH CHECK (id::text = current_setting('app.current_user_id', true));
    """)

    # Create policy to allow initial user creation (when no user_id is set)
    # This allows signup to work before a user is authenticated
    op.execute("""
        CREATE POLICY user_signup_policy ON users
            FOR INSERT
            WITH CHECK (current_setting('app.current_user_id', true) IS NULL
                       OR current_setting('app.current_user_id', true) = '');
    """)


def downgrade() -> None:
    """Drop users table."""
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
