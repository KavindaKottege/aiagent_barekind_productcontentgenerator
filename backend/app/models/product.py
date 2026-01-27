"""Product model for storing product data from Excel uploads."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    """Product model for storing individual product data with variant support."""

    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Mapped Faire columns (core fields)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_token: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status and description
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Variant info (Option 1)
    option_type: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., "Color", "Size"
    option_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., "Black", "Small"

    # Variant info (Option 2)
    option_2_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    option_2_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Variant info (Option 3)
    option_3_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    option_3_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Pricing (USD)
    wholesale_price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    retail_price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Product metadata
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_of_origin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    made_to_order: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Images (array of URLs stored as JSONB)
    images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Unmapped columns stored as JSONB (preserved for Phase 7 export)
    unmapped_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Row index for export ordering (original position in Excel)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships - use lazy="raise" to prevent async lazy loading issues
    client: Mapped["Client"] = relationship(back_populates="products", lazy="raise")
    user: Mapped["User"] = relationship(lazy="raise")
    group: Mapped["ProductGroup"] = relationship(back_populates="products", lazy="raise")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, product_name={self.product_name}, sku={self.sku}, row_index={self.row_index})>"
