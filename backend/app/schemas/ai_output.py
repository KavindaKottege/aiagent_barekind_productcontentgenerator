"""Structured output schemas for AI generation."""

from pydantic import BaseModel, Field, field_validator


class ProductContent(BaseModel):
    """
    Structured output schema for product content generation.

    Used with LangChain's with_structured_output() to guarantee valid JSON
    responses with character limit validation.
    """

    title: str = Field(
        ...,
        description="Product title, must be 30-60 characters including spaces",
    )
    description: str = Field(
        ...,
        description="Product description, must be 2000-3000 characters including spaces",
    )

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, v: str) -> str:
        """Validate title is 30-60 characters."""
        char_count = len(v)
        if not 30 <= char_count <= 60:
            raise ValueError(
                f"Title must be 30-60 characters, got {char_count}. "
                f"Title: '{v[:50]}...'" if len(v) > 50 else f"Title: '{v}'"
            )
        return v

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str) -> str:
        """Validate description is 2000-3000 characters."""
        char_count = len(v)
        if not 2000 <= char_count <= 3000:
            raise ValueError(
                f"Description must be 2000-3000 characters, got {char_count}. "
                f"{'Too short' if char_count < 2000 else 'Too long'}"
            )
        return v


class ProductContentLenient(BaseModel):
    """
    Lenient version for storing failed attempts.

    No validators - stores whatever the model generated for audit trail.
    """

    title: str | None = None
    description: str | None = None


class TitleContent(BaseModel):
    """
    Task 1: Title generation structured output.

    Generates only the product title. Validation happens in service with settings.
    """

    title: str = Field(..., description="Product title")


class DescriptionContent(BaseModel):
    """
    Task 2: Description generation structured output.

    Generates only the product description. Validation happens in service with settings.
    """

    description: str = Field(..., description="Product description")
