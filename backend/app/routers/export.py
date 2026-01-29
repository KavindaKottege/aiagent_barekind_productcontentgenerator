"""Export API endpoints for downloading product data as Excel."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.client import Client
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.user import User
from app.schemas.export import ExportStatsResponse
from app.services.excel_exporter import ExcelExporter
from app.services.column_mapper import ExactColumnMapper
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/export", tags=["export"])


async def _get_client(
    client_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Client:
    """Validate client ownership and return the client."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return client


@router.get("/{client_id}/stats", response_model=ExportStatsResponse)
async def get_export_stats(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ExportStatsResponse:
    """Get export statistics for a client's products.

    Returns counts by status for the export confirmation dialog:
    - total: all product groups
    - not_generated: groups where status != 'generated'
    - approved: groups with review_status in ('approved', 'edited')
    - rejected: groups with review_status == 'rejected'
    - pending: generated groups not yet approved/rejected
    """
    await _get_client(client_id, current_user, db)

    # Count all groups
    total_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
        )
    )
    total = total_result.scalar() or 0

    # Count approved (review_status in approved/edited)
    approved_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status.in_(["approved", "edited"]),
        )
    )
    approved = approved_result.scalar() or 0

    # Count rejected
    rejected_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "rejected",
        )
    )
    rejected = rejected_result.scalar() or 0

    # Count not generated (status != 'generated')
    not_generated_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.status != "generated",
        )
    )
    not_generated = not_generated_result.scalar() or 0

    # Pending = total - approved - rejected - not_generated
    pending = total - approved - rejected - not_generated

    return ExportStatsResponse(
        total=total,
        not_generated=not_generated,
        approved=approved,
        pending=pending,
        rejected=rejected,
    )


@router.get("/{client_id}")
async def export_products(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    include_pending: bool = Query(False, description="Include content pending approval"),
    db: AsyncSession = Depends(get_db),
):
    """Export products as an Excel file.

    Downloads a .xlsx file with all products for the client.
    Only approved (and optionally pending) products have their
    Product Name and Description columns updated with generated content.
    All other columns and rejected/non-generated products keep original values.
    """
    client = await _get_client(client_id, current_user, db)

    # Check that there are approved products
    approved_count_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status.in_(["approved", "edited"]),
        )
    )
    approved_count = approved_count_result.scalar() or 0

    if approved_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No approved products to export",
        )

    # Query all products for client with eager-loaded groups, ordered by row_index
    result = await db.execute(
        select(Product)
        .where(Product.client_id == client_id)
        .options(selectinload(Product.group))
        .order_by(Product.row_index)
    )
    products = result.scalars().all()

    # Determine column order
    column_order = _build_column_order(client, products)

    # Build export data
    products_data = _build_products_data(products)

    # Generate Excel
    exporter = ExcelExporter()
    buffer = exporter.export(products_data, column_order, include_pending=include_pending)

    # Build filename
    brand_name = client.brand_name or "export"
    # Sanitize brand name for filename (replace spaces, remove special chars)
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in brand_name)
    safe_name = safe_name.strip().replace(" ", "_")
    filename = f"{safe_name}_products_{date.today().isoformat()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _build_column_order(client: Client, products: list[Product]) -> list[str]:
    """Build the column order for the export.

    Uses client.excel_column_order if available (stored during upload).
    Falls back to deriving from COLUMN_MAP values + unmapped_data keys.
    """
    if client.excel_column_order:
        return client.excel_column_order

    # Fallback: derive from mapped columns + unmapped data keys
    # Start with all mapped column headers in COLUMN_MAP order
    mapped_headers = list(ExactColumnMapper.COLUMN_MAP.values())

    # Collect unmapped column keys from all products (preserving first-seen order)
    unmapped_keys: list[str] = []
    seen_keys: set[str] = set()
    for product in products:
        if product.unmapped_data:
            for key in product.unmapped_data.keys():
                if key not in seen_keys:
                    unmapped_keys.append(key)
                    seen_keys.add(key)

    return mapped_headers + unmapped_keys


def _build_products_data(products: list[Product]) -> list[dict]:
    """Build product data dicts with group info for the exporter.

    Each dict contains all mapped field values, unmapped_data,
    and group-level fields needed for content substitution.
    """
    products_data = []
    for product in products:
        group = product.group

        data = {
            # Core mapped fields
            "product_name": product.product_name,
            "product_token": product.product_token,
            "sku": product.sku,
            "status": product.status,
            "description": product.description,
            "option_type": product.option_type,
            "option_name": product.option_name,
            "option_2_name": product.option_2_name,
            "option_2_value": product.option_2_value,
            "option_3_name": product.option_3_name,
            "option_3_value": product.option_3_value,
            "product_type": product.product_type,
            "country_of_origin": product.country_of_origin,
            "made_to_order": product.made_to_order,
            "images": product.images,
            "wholesale_price_usd": product.wholesale_price_usd,
            "retail_price_usd": product.retail_price_usd,
            # Unmapped data
            "unmapped_data": product.unmapped_data or {},
            # Group-level fields for content substitution
            "review_status": group.review_status if group else None,
            # Use group status field name carefully - the Product model has
            # a 'status' field too (product status), but we need group.status
            # for generation status. Store it separately.
        }

        # Store group status separately to avoid collision with product.status
        if group:
            data["group_status"] = group.status
            data["generated_title"] = group.generated_title
            data["generated_description"] = group.generated_description
            data["edited_title"] = group.edited_title
            data["edited_description"] = group.edited_description
        else:
            data["group_status"] = None
            data["generated_title"] = None
            data["generated_description"] = None
            data["edited_title"] = None
            data["edited_description"] = None

        products_data.append(data)

    return products_data
