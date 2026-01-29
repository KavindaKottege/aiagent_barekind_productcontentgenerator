"""Client model for brand profile management."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Client(Base):
    """Client model for storing brand profiles and custom prompts."""

    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Brand info (only brand_name required)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI input field selection (persists per client)
    ai_input_fields: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="List of product field names to include in AI prompts"
    )

    # Original Excel column order (persists during upload for export reconstruction)
    excel_column_order: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Original Excel column headers in order, stored during upload"
    )

    # Custom prompts (optional overrides of app defaults)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    task1_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    task2_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    user: Mapped["User"] = relationship(back_populates="clients", lazy="raise")
    products: Mapped[list["Product"]] = relationship(
        back_populates="client",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    product_groups: Mapped[list["ProductGroup"]] = relationship(
        back_populates="client",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, brand_name={self.brand_name}, user_id={self.user_id})>"
