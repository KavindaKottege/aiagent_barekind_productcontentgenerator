"""Pydantic schemas for settings operations."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdate(BaseModel):
    """Schema for updating settings."""

    openai_api_key: str | None = None
    default_system_prompt: str | None = None
    default_task1_prompt: str | None = None
    default_task2_prompt: str | None = None
    default_task3_prompt: str | None = None
    default_task4_prompt: str | None = None
    ai_model: str | None = None
    ai_temperature: Decimal | None = Field(None, ge=0, le=1)
    generation_soft_cap: Decimal | None = Field(None, ge=0)

    # Per-task attribute settings
    task1_default_attributes: list[str] | None = None
    task1_mandatory_attributes: list[str] | None = None
    task2_default_attributes: list[str] | None = None
    task2_mandatory_attributes: list[str] | None = None
    task3_default_attributes: list[str] | None = None
    task3_mandatory_attributes: list[str] | None = None
    task4_default_attributes: list[str] | None = None
    task4_mandatory_attributes: list[str] | None = None

    # Length settings
    task1_min_length: int | None = None
    task1_max_length: int | None = None
    task1_target_length: int | None = None
    task2_min_length: int | None = None
    task2_max_length: int | None = None
    task2_target_length: int | None = None


class SettingsResponse(BaseModel):
    """Schema for settings response."""

    openai_api_key: str | None
    has_api_key: bool
    default_system_prompt: str | None
    default_task1_prompt: str | None
    default_task2_prompt: str | None
    default_task3_prompt: str | None
    default_task4_prompt: str | None
    ai_model: str = "gpt-5.2"
    ai_temperature: Decimal = Decimal("0.7")
    generation_soft_cap: Decimal = Decimal("500.00")

    # Per-task attribute settings
    task1_default_attributes: list[str] | None = None
    task1_mandatory_attributes: list[str] | None = None
    task2_default_attributes: list[str] | None = None
    task2_mandatory_attributes: list[str] | None = None
    task3_default_attributes: list[str] | None = None
    task3_mandatory_attributes: list[str] | None = None
    task4_default_attributes: list[str] | None = None
    task4_mandatory_attributes: list[str] | None = None

    # Length settings
    task1_min_length: int | None = None
    task1_max_length: int | None = None
    task1_target_length: int | None = None
    task2_min_length: int | None = None
    task2_max_length: int | None = None
    task2_target_length: int | None = None

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


class TaskSettingsResponse(BaseModel):
    """Response schema for AI task settings."""

    model_config = ConfigDict(from_attributes=True)

    # System prompt (global)
    default_system_prompt: str | None = None

    # Task prompts
    default_task1_prompt: str | None = None
    default_task2_prompt: str | None = None
    default_task3_prompt: str | None = None
    default_task4_prompt: str | None = None

    # Per-task attribute settings
    task1_default_attributes: list[str] | None = None
    task1_mandatory_attributes: list[str] | None = None
    task2_default_attributes: list[str] | None = None
    task2_mandatory_attributes: list[str] | None = None
    task3_default_attributes: list[str] | None = None
    task3_mandatory_attributes: list[str] | None = None
    task4_default_attributes: list[str] | None = None
    task4_mandatory_attributes: list[str] | None = None

    # Length settings for Task 1 & 2
    task1_min_length: int | None = None
    task1_max_length: int | None = None
    task1_target_length: int | None = None
    task2_min_length: int | None = None
    task2_max_length: int | None = None
    task2_target_length: int | None = None


class TaskSettingsUpdate(BaseModel):
    """Update schema for AI task settings."""

    # System prompt (global)
    default_system_prompt: str | None = None

    # Task prompts
    default_task1_prompt: str | None = None
    default_task2_prompt: str | None = None
    default_task3_prompt: str | None = None
    default_task4_prompt: str | None = None

    # Per-task attribute settings
    task1_default_attributes: list[str] | None = None
    task1_mandatory_attributes: list[str] | None = None
    task2_default_attributes: list[str] | None = None
    task2_mandatory_attributes: list[str] | None = None
    task3_default_attributes: list[str] | None = None
    task3_mandatory_attributes: list[str] | None = None
    task4_default_attributes: list[str] | None = None
    task4_mandatory_attributes: list[str] | None = None

    # Length settings for Task 1 & 2
    task1_min_length: int | None = None
    task1_max_length: int | None = None
    task1_target_length: int | None = None
    task2_min_length: int | None = None
    task2_max_length: int | None = None
    task2_target_length: int | None = None
