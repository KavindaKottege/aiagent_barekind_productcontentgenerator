"""Pydantic schemas for Product and ProductGroup API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductGroupBase(BaseModel):
    """Base schema for ProductGroup."""

    product_name: str
    product_token: str
    sku: str


class ProductGroupCreate(ProductGroupBase):
    """Schema for creating a new product group."""

    client_id: UUID
    variant_count: int = 1


class ProductGroupPublic(ProductGroupBase):
    """Schema for product group response."""

    id: UUID
    variant_count: int
    status: str
    generated_title: str | None
    generated_description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    """Base schema for Product."""

    product_name: str
    product_token: str
    sku: str
    status: str | None = None
    description: str | None = None
    option_type: str | None = None  # e.g., "Color", "Size"
    option_name: str | None = None  # e.g., "Black", "Small"
    product_type: str | None = None
    country_of_origin: str | None = None
    made_to_order: bool | None = None
    images: list[str] | None = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    client_id: UUID
    group_id: UUID
    unmapped_data: dict = Field(default_factory=dict)
    row_index: int


class ProductPublic(ProductBase):
    """Schema for product response."""

    id: UUID
    group_id: UUID
    unmapped_data: dict
    row_index: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductGroupWithVariants(ProductGroupPublic):
    """Schema for product group with its variants (for UI expand/collapse)."""

    variants: list[ProductPublic]


class UploadResponse(BaseModel):
    """Schema for Excel upload response."""

    total_rows: int = Field(..., description="Original Excel rows uploaded")
    product_groups: int = Field(..., description="Unique products after grouping")
    variant_groups: int = Field(..., description="Products with multiple variants")
    standalone_products: int = Field(..., description="Products with single variant")
    mapped_columns: dict[str, str] = Field(..., description="Field -> Excel column name mapping")
    unmapped_columns: list[str] = Field(..., description="Excel columns not mapped to fields")
