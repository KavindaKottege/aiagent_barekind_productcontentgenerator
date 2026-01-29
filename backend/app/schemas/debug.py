"""Pydantic schemas for the admin debug log API."""

from pydantic import BaseModel, ConfigDict


class DebugLogEntry(BaseModel):
    """Schema for a single generation audit log entry exposed via the debug API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    product_group_id: str
    attempt_number: int
    prompt_used: str
    model_version: str
    temperature: float
    input_tokens: int
    output_tokens: int
    cost: str
    duration_ms: int
    success: bool
    error_message: str | None
    generated_title: str | None
    generated_description: str | None
    title_length: int | None
    description_length: int | None
    created_at: str
