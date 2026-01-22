"""AppSettings model for application-wide configuration."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
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
    default_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_task1_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_task2_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

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
