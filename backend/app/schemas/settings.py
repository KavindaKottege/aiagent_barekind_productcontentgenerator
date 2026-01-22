"""Pydantic schemas for settings operations."""

from pydantic import BaseModel, ConfigDict


class SettingsUpdate(BaseModel):
    """Schema for updating settings."""

    openai_api_key: str | None = None
    default_system_prompt: str | None = None
    default_task1_prompt: str | None = None
    default_task2_prompt: str | None = None


class SettingsResponse(BaseModel):
    """Schema for settings response."""

    openai_api_key: str | None
    has_api_key: bool
    default_system_prompt: str | None
    default_task1_prompt: str | None
    default_task2_prompt: str | None

    model_config = ConfigDict(from_attributes=True)

    @property
    def has_api_key(self) -> bool:
        """Compute whether API key is configured."""
        return self.openai_api_key is not None and self.openai_api_key != ""


class HasApiKeyResponse(BaseModel):
    """Public response indicating if API key is configured."""

    has_api_key: bool
