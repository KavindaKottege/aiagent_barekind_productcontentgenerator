"""Pydantic schemas for generation API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class GenerateRequest(BaseModel):
    """Request to start generation job for a client."""
    client_id: UUID = Field(..., description="Client ID to generate content for")


class PauseJobRequest(BaseModel):
    """Request to pause a running job."""
    job_id: UUID = Field(..., description="Job ID to pause")


class ResumeJobRequest(BaseModel):
    """Request to resume a paused job."""
    job_id: UUID = Field(..., description="Job ID to resume")


class CancelJobRequest(BaseModel):
    """Request to cancel a job."""
    job_id: UUID = Field(..., description="Job ID to cancel")


# Response schemas
class GenerationProgressResponse(BaseModel):
    """Real-time progress update for generation job."""
    job_id: UUID
    status: str  # pending, running, paused, completed, failed, cancelled
    total_count: int
    completed_count: int
    success_count: int
    failed_count: int
    total_cost: Decimal
    projected_cost: Decimal
    elapsed_seconds: int | None = None
    estimated_seconds_remaining: int | None = None

    class Config:
        from_attributes = True


class GenerationJobSummary(BaseModel):
    """Summary of completed generation job."""
    total_products: int
    successful: int
    failed: int
    total_cost: Decimal
    elapsed_seconds: int

    class Config:
        from_attributes = True


class AttemptResult(BaseModel):
    """Result of a single generation attempt."""
    success: bool
    error: str | None = None


class GenerationJobResponse(BaseModel):
    """Response for generation job details."""
    id: UUID
    client_id: UUID
    user_id: UUID
    status: str
    status_reason: str | None
    total_count: int
    completed_count: int
    success_count: int
    failed_count: int
    total_cost: Decimal
    projected_cost: Decimal
    total_input_tokens: int
    total_cached_input_tokens: int
    total_output_tokens: int
    total_input_cost: Decimal
    total_cached_input_cost: Decimal
    total_output_cost: Decimal
    elapsed_seconds: int
    started_at: datetime | None
    completed_at: datetime | None
    paused_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    # Current task tracking for real-time UI updates
    current_product_name: str | None = None
    current_task: str | None = None  # "title" or "description"
    task1_attempts: list[AttemptResult] | None = None
    task2_attempts: list[AttemptResult] | None = None

    class Config:
        from_attributes = True


class GenerationAuditResponse(BaseModel):
    """Response for generation audit record."""
    id: UUID
    job_id: UUID
    product_group_id: UUID
    model_version: str
    temperature: Decimal
    prompt_used: str
    generated_title: str | None
    generated_description: str | None
    input_tokens: int
    output_tokens: int
    cost: Decimal
    title_length: int | None
    description_length: int | None
    attempt_number: int
    success: bool
    error_message: str | None
    duration_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response for list of jobs."""
    jobs: list[GenerationJobResponse]
    total: int


class AuditListResponse(BaseModel):
    """Response for list of audit records."""
    audits: list[GenerationAuditResponse]
    total: int


class GenerationJobCreate(BaseModel):
    """Request to create and start a new generation job."""
    client_id: UUID = Field(..., description="Client ID to generate content for")


class CostCapDialogResponse(BaseModel):
    """User response to soft cap dialog."""
    continue_generation: bool = Field(..., description="True to continue despite cost, False to stop")
