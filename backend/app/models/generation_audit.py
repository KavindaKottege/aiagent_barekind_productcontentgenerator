"""GenerationAudit model for tracking per-product generation attempts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class GenerationAudit(Base):
    """GenerationAudit model for storing full audit trail of generation attempts."""

    __tablename__ = "generation_audits"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_group_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Generation metadata
    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., "gpt-5.2", "gpt-4o"
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
    )  # e.g., 0.7

    # Prompt and output
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)
    generated_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Token and cost tracking
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0"),
    )

    # Character counts (for validation tracking)
    title_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Retry and status tracking
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )  # 1 for first attempt, 2+ for retries
    success: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Duration tracking
    duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )  # Generation duration in milliseconds

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships - use lazy="raise" to prevent async lazy loading issues
    job: Mapped["GenerationJob"] = relationship(back_populates="audit_records", lazy="raise")
    product_group: Mapped["ProductGroup"] = relationship(lazy="raise")

    def __repr__(self) -> str:
        return f"<GenerationAudit(id={self.id}, job_id={self.job_id}, attempt={self.attempt_number}, success={self.success})>"
