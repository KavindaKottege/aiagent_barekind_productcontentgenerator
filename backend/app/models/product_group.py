"""ProductGroup model for variant grouping."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ProductGroup(Base):
    """ProductGroup model for grouping product variants with shared content."""

    __tablename__ = "product_groups"

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

    # Grouping keys (product identifier)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_token: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(255), nullable=False)

    # Variant metadata
    variant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # Generated content (filled by Phase 4)
    generated_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Edited content (filled by Phase 5 review)
    edited_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    edited_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", server_default="pending")

    # Review status tracking (Phase 5)
    review_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # approved, rejected, edited
    ai_review_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # ai_approved, ai_rejected
    ai_review_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_review_safety_flags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list, server_default="[]")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    client: Mapped["Client"] = relationship(back_populates="product_groups", lazy="raise")
    user: Mapped["User"] = relationship(lazy="raise")
    products: Mapped[list["Product"]] = relationship(
        back_populates="group",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ProductGroup(id={self.id}, product_name={self.product_name}, variant_count={self.variant_count})>"
