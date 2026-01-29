"""Export API endpoints for downloading product data as Excel."""

from datetime import date
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.product_group import ProductGroup
from app.models.user import User
from app.schemas.export import ExportStatsResponse
from app.services.excel_exporter import ExcelExporter
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/export", tags=["export"])

# Path to the uploads directory (same location used by upload endpoint)
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


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

    Returns counts by status for the export confirmation dialog.
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

    Opens the ORIGINAL uploaded Excel (preserving formatting, extra sheets,
    column positions) and only overwrites Product Name and Description cells
    for approved product groups.  Everything else stays identical.
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

    # Locate the original uploaded file
    original_file = UPLOADS_DIR / f"{client_id}.xlsx"
    if not original_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original Excel file not found. Please re-upload the product file.",
        )

    # Build lookup: (product_name, product_token, sku) → group content dict
    groups_result = await db.execute(
        select(ProductGroup).where(ProductGroup.client_id == client_id)
    )
    groups = groups_result.scalars().all()

    groups_lookup: dict[tuple[str, str, str], dict] = {}
    for g in groups:
        key = (g.product_name, g.product_token, g.sku)
        groups_lookup[key] = {
            "review_status": g.review_status,
            "status": g.status,
            "generated_title": g.generated_title,
            "generated_description": g.generated_description,
            "edited_title": g.edited_title,
            "edited_description": g.edited_description,
        }

    # Patch the original Excel
    exporter = ExcelExporter()
    buffer = exporter.export(original_file, groups_lookup, include_pending=include_pending)

    # Build filename
    brand_name = client.brand_name or "export"
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
