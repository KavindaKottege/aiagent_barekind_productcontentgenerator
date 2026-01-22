"""Pydantic schemas for Client API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    """Schema for creating a new client."""

    brand_name: str = Field(..., min_length=1, max_length=255)
    story: str | None = None
    tone: str | None = Field(None, max_length=255)
    language: str | None = Field(None, max_length=100)
    guidelines: str | None = None
    system_prompt: str | None = None
    task1_prompt: str | None = None
    task2_prompt: str | None = None


class ClientUpdate(BaseModel):
    """Schema for updating a client (all fields optional)."""

    brand_name: str | None = Field(None, min_length=1, max_length=255)
    story: str | None = None
    tone: str | None = Field(None, max_length=255)
    language: str | None = Field(None, max_length=100)
    guidelines: str | None = None
    system_prompt: str | None = None
    task1_prompt: str | None = None
    task2_prompt: str | None = None


class ClientPublic(BaseModel):
    """Schema for client response."""

    id: UUID
    user_id: UUID
    brand_name: str
    story: str | None
    tone: str | None
    language: str | None
    guidelines: str | None
    system_prompt: str | None
    task1_prompt: str | None
    task2_prompt: str | None
    has_custom_prompts: bool  # Computed field
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_computed(cls, client) -> "ClientPublic":
        """Create response with computed has_custom_prompts field."""
        has_custom = any(
            [
                client.system_prompt,
                client.task1_prompt,
                client.task2_prompt,
            ]
        )
        return cls(
            id=client.id,
            user_id=client.user_id,
            brand_name=client.brand_name,
            story=client.story,
            tone=client.tone,
            language=client.language,
            guidelines=client.guidelines,
            system_prompt=client.system_prompt,
            task1_prompt=client.task1_prompt,
            task2_prompt=client.task2_prompt,
            has_custom_prompts=has_custom,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )
