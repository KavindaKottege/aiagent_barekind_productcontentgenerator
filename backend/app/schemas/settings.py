"""Pydantic schemas for settings operations."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdate(BaseModel):
    """Schema for updating settings."""

    openai_api_key: str | None = None
    default_system_prompt: str | None = None
    default_task1_prompt: str | None = None
    default_task2_prompt: str | None = None
    ai_model: str | None = None
    ai_temperature: Decimal | None = Field(None, ge=0, le=1)
    generation_soft_cap: Decimal | None = Field(None, ge=0)


class SettingsResponse(BaseModel):
    """Schema for settings response."""

    openai_api_key: str | None
    has_api_key: bool
    default_system_prompt: str | None
    default_task1_prompt: str | None
    default_task2_prompt: str | None
    ai_model: str = "gpt-5.2"
    ai_temperature: Decimal = Decimal("0.7")
    generation_soft_cap: Decimal = Decimal("500.00")

    model_config = ConfigDict(from_attributes=True)

    @property
    def has_api_key(self) -> bool:
        """Compute whether API key is configured."""
        return self.openai_api_key is not None and self.openai_api_key != ""


class HasApiKeyResponse(BaseModel):
    """Public response indicating if API key is configured."""

    has_api_key: bool


class GenerationSettingsResponse(BaseModel):
    """Response schema for generation-specific settings."""

    model_config = ConfigDict(from_attributes=True)

    ai_model: str
    ai_temperature: Decimal
    generation_soft_cap: Decimal


class GenerationSettingsUpdate(BaseModel):
    """Update schema for generation settings."""

    ai_model: str | None = None
    ai_temperature: Decimal | None = Field(None, ge=0, le=1)
    generation_soft_cap: Decimal | None = Field(None, ge=0)
