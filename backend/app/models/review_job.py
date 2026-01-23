"""ReviewJob model for tracking AI review jobs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ReviewJob(Base):
    """ReviewJob model for tracking AI review job status and progress."""

    __tablename__ = "review_jobs"

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

    # Cost tracking (Decimal for precision)
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    # Time tracking
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

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

    def __repr__(self) -> str:
        return f"<ReviewJob(id={self.id}, status={self.status}, completed={self.completed_count}/{self.total_count})>"
