"""AppSettings model for application-wide configuration."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSettings(Base):
    """
    Application settings model.

    This table follows a singleton pattern - only one row with id=1 is expected.
    Stores application-wide configuration like API keys, default AI prompts,
    and generation settings.
    """

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Default AI prompts (can be overridden per-client)
    # Task 1: Product Title Generation
    # Task 2: Product Description Generation
    # Task 3: Generated Title Review
    # Task 4: Generated Description Review
    default_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_task1_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_task2_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_task3_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_task4_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Per-task attribute settings (JSON arrays of attribute IDs)
    # Default: pre-selected attributes when starting generation
    # Mandatory: always-selected attributes that can't be unchecked
    task1_default_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task1_mandatory_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task2_default_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task2_mandatory_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task3_default_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task3_mandatory_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task4_default_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    task4_mandatory_attributes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Length settings for Task 1 (title generation)
    task1_min_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task1_max_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task1_target_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Length settings for Task 2 (description generation)
    task2_min_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task2_max_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task2_target_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI Generation settings
    ai_model: Mapped[str] = mapped_column(
        String(50), nullable=False, default="gpt-5.2", server_default="gpt-5.2"
    )
    ai_temperature: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.7"), server_default="0.7"
    )
    generation_soft_cap: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("500.00"), server_default="500.00"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
