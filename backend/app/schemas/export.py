"""Export-related Pydantic schemas."""

from pydantic import BaseModel


class ExportStatsResponse(BaseModel):
    """Response schema for export statistics endpoint."""

    total: int
    not_generated: int
    approved: int
    pending: int
    rejected: int
