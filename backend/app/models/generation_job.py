"""GenerationJob model for tracking AI generation jobs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class GenerationJob(Base):
    """GenerationJob model for tracking generation job status and progress."""

    __tablename__ = "generation_jobs"

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

    # Job status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )  # pending, running, paused, completed, failed, cancelled

    # Progress tracking
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Cost tracking (Decimal for precision)
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    projected_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    # Token tracking
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_cached_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Cost breakdown
    total_input_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    total_cached_input_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    total_output_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    # Soft cap threshold - the cost at which to next trigger soft cap pause
    # For new jobs, this is initialized to the soft cap value from settings
    # When user acknowledges soft cap, this is set to current_cost + soft_cap
    soft_cap_threshold: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    # Time tracking
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Cumulative running time (excludes paused time)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Status reason (for pause, cancel, soft cap, etc.)
    status_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Target product group for single-product generation (null = batch generation)
    target_product_group_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Current processing state (for real-time UI updates)
    current_product_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    current_task: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "title" or "description"

    # Attempt tracking for current product (JSON arrays)
    # Format: [{"success": true/false, "error": "message or null"}, ...]
    task1_attempts: Mapped[list | None] = mapped_column(JSON, nullable=True)
    task2_attempts: Mapped[list | None] = mapped_column(JSON, nullable=True)

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
    client: Mapped["Client"] = relationship(lazy="raise")
    user: Mapped["User"] = relationship(lazy="raise")
    audit_records: Mapped[list["GenerationAudit"]] = relationship(
        back_populates="job",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GenerationJob(id={self.id}, status={self.status}, completed={self.completed_count}/{self.total_count})>"
