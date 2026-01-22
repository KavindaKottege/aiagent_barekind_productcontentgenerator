"""Create products and product_groups tables

Revision ID: 005
Revises: 004
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create product_groups and products tables."""
    # Create product_groups table first (parent in relationship)
    op.execute("""
        CREATE TABLE product_groups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            product_name VARCHAR(500) NOT NULL,
            product_token VARCHAR(255) NOT NULL,
            sku VARCHAR(255) NOT NULL,
            variant_count INTEGER NOT NULL DEFAULT 1,
            generated_title VARCHAR(255),
            generated_description TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Indexes on product_groups
    op.execute("""
        CREATE INDEX ix_product_groups_client_id ON product_groups (client_id);
    """)
    op.execute("""
        CREATE INDEX ix_product_groups_user_id ON product_groups (user_id);
    """)
    # Unique constraint on grouping keys per client (prevent duplicate groups)
    op.execute("""
        CREATE UNIQUE INDEX ix_product_groups_unique_group
        ON product_groups (client_id, product_name, product_token, sku);
    """)

    # Create products table (references product_groups)
    op.execute("""
        CREATE TABLE products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            group_id UUID NOT NULL REFERENCES product_groups(id) ON DELETE CASCADE,
            product_name VARCHAR(500) NOT NULL,
            product_token VARCHAR(255) NOT NULL,
            sku VARCHAR(255) NOT NULL,
            status VARCHAR(100),
            description TEXT,
            option_name VARCHAR(255),
            product_type VARCHAR(255),
            country_of_origin VARCHAR(100),
            made_to_order BOOLEAN,
            images JSONB,
            unmapped_data JSONB NOT NULL DEFAULT '{}',
            row_index INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Indexes on products
    op.execute("""
        CREATE INDEX ix_products_client_id ON products (client_id);
    """)
    op.execute("""
        CREATE INDEX ix_products_user_id ON products (user_id);
    """)
    op.execute("""
        CREATE INDEX ix_products_group_id ON products (group_id);
    """)
    # Index for export ordering (by client and original row position)
    op.execute("""
        CREATE INDEX ix_products_client_row ON products (client_id, row_index);
    """)


def downgrade() -> None:
    """Drop products and product_groups tables."""
    # Drop in reverse order (child first, then parent)
    op.drop_table('products')
    op.drop_table('product_groups')
