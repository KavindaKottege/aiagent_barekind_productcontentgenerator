"""Review API endpoints for manual content review workflow."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.user import User
from app.schemas.review import (
    EditContentRequest,
    ProductGroupReview,
    ReviewActionRequest,
    ReviewActionResponse,
    ReviewStatsResponse,
    UndoReviewRequest,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/{client_id}/products", response_model=list[ProductGroupReview])
async def get_products_for_review(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[str, Query(description="Filter by review status")] = "all",
    db: AsyncSession = Depends(get_db),
) -> list[ProductGroupReview]:
    """
    Get list of product groups for review.

    - Filters: all, pending, approved, rejected, ai_approved, ai_rejected, edited
    - Only returns products with status='generated'
    - Orders by row_index for consistent queue
    """
    # Validate client belongs to user
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

    # Build query for product groups
    query = select(ProductGroup).where(
        ProductGroup.client_id == client_id,
        ProductGroup.status == "generated",  # Only show generated products
    )

    # Apply status filter
    if status_filter == "pending":
        query = query.where(ProductGroup.review_status.is_(None))
    elif status_filter == "approved":
        query = query.where(ProductGroup.review_status == "approved")
    elif status_filter == "rejected":
        query = query.where(ProductGroup.review_status == "rejected")
    elif status_filter == "edited":
        query = query.where(ProductGroup.review_status == "edited")
    elif status_filter == "ai_approved":
        query = query.where(ProductGroup.ai_review_status == "ai_approved")
    elif status_filter == "ai_rejected":
        query = query.where(ProductGroup.ai_review_status == "ai_rejected")
    # 'all' = no filter

    query = query.order_by(ProductGroup.created_at.desc())

    result = await db.execute(query)
    product_groups = result.scalars().all()

    # For each group, fetch first product for images and original_data
    review_list = []
    for group in product_groups:
        # Get first product in group for images and original data
        product_result = await db.execute(
            select(Product)
            .where(Product.group_id == group.id)
            .order_by(Product.row_index)
            .limit(1)
        )
        first_product = product_result.scalar_one_or_none()

        # Build original_data dict
        original_data = {}
        if first_product:
            original_data = {
                "description": first_product.description or "",
                "product_type": first_product.product_type or "",
                "option_name": first_product.option_name or "",
                "country_of_origin": first_product.country_of_origin or "",
                "made_to_order": first_product.made_to_order or "",
            }

        review_list.append(
            ProductGroupReview(
                id=group.id,
                product_name=group.product_name,
                product_token=group.product_token,
                sku=group.sku,
                variant_count=group.variant_count,
                generated_title=group.generated_title,
                generated_description=group.generated_description,
                edited_title=group.edited_title,
                edited_description=group.edited_description,
                status=group.status,
                review_status=group.review_status,
                ai_review_status=group.ai_review_status,
                ai_review_reason=group.ai_review_reason,
                ai_review_safety_flags=group.ai_review_safety_flags or [],
                images=first_product.images if first_product else [],
                original_data=original_data,
                row_index=first_product.row_index if first_product else 0,
                reviewed_at=group.reviewed_at,
                ai_reviewed_at=group.ai_reviewed_at,
            )
        )

    return review_list


@router.get("/{client_id}/product/{product_group_id}", response_model=ProductGroupReview)
async def get_product_for_review(
    client_id: UUID,
    product_group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ProductGroupReview:
    """Get single product group for review UI."""
    # Validate client belongs to user
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

    # Get product group
    result = await db.execute(
        select(ProductGroup).where(
            ProductGroup.id == product_group_id,
            ProductGroup.client_id == client_id,
        )
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Get first product for images and original data
    product_result = await db.execute(
        select(Product)
        .where(Product.group_id == group.id)
        .order_by(Product.row_index)
        .limit(1)
    )
    first_product = product_result.scalar_one_or_none()

    # Build original_data dict
    original_data = {}
    if first_product:
        original_data = {
            "description": first_product.description or "",
            "product_type": first_product.product_type or "",
            "option_name": first_product.option_name or "",
            "country_of_origin": first_product.country_of_origin or "",
            "made_to_order": first_product.made_to_order or "",
        }

    return ProductGroupReview(
        id=group.id,
        product_name=group.product_name,
        product_token=group.product_token,
        sku=group.sku,
        variant_count=group.variant_count,
        generated_title=group.generated_title,
        generated_description=group.generated_description,
        edited_title=group.edited_title,
        edited_description=group.edited_description,
        status=group.status,
        review_status=group.review_status,
        ai_review_status=group.ai_review_status,
        ai_review_reason=group.ai_review_reason,
        ai_review_safety_flags=group.ai_review_safety_flags or [],
        images=first_product.images if first_product else [],
        original_data=original_data,
        row_index=first_product.row_index if first_product else 0,
        reviewed_at=group.reviewed_at,
        ai_reviewed_at=group.ai_reviewed_at,
    )


@router.post("/approve", response_model=ReviewActionResponse)
async def approve_product(
    request: ReviewActionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Approve a product group.

    Sets review_status='approved' and reviewed_at timestamp.
    Returns next unreviewed product for auto-advance.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this product",
        )

    # Update review status
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status="approved",
            reviewed_at=func.now(),
        )
    )
    await db.commit()

    # Find next unreviewed product (same client, row_index order)
    next_result = await db.execute(
        select(ProductGroup)
        .join(Product, Product.group_id == ProductGroup.id)
        .where(
            ProductGroup.client_id == group.client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
        .order_by(Product.row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return ReviewActionResponse(
        success=True,
        message="Product approved successfully",
        next_product_id=next_group.id if next_group else None,
    )


@router.post("/reject", response_model=ReviewActionResponse)
async def reject_product(
    request: ReviewActionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Reject a product group.

    Sets review_status='rejected' and reviewed_at timestamp.
    Returns next unreviewed product for auto-advance.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this product",
        )

    # Update review status
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status="rejected",
            reviewed_at=func.now(),
        )
    )
    await db.commit()

    # Find next unreviewed product (same client, row_index order)
    next_result = await db.execute(
        select(ProductGroup)
        .join(Product, Product.group_id == ProductGroup.id)
        .where(
            ProductGroup.client_id == group.client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
        .order_by(Product.row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return ReviewActionResponse(
        success=True,
        message="Product rejected successfully",
        next_product_id=next_group.id if next_group else None,
    )


@router.post("/edit", response_model=ReviewActionResponse)
async def edit_product_content(
    request: EditContentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Save edited content for a product group.

    Sets edited_title, edited_description, and review_status='edited'.
    User must explicitly approve after editing.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this product",
        )

    # Update edited content
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            edited_title=request.edited_title,
            edited_description=request.edited_description,
            review_status="edited",
        )
    )
    await db.commit()

    return ReviewActionResponse(
        success=True,
        message="Edits saved successfully. Click Approve to finalize.",
        next_product_id=None,  # Don't auto-advance after edit
    )


@router.post("/undo", response_model=ReviewActionResponse)
async def undo_review(
    request: UndoReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Undo a review action.

    Clears review_status and reviewed_at.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this product",
        )

    # Revert review status
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status=None,
            reviewed_at=None,
        )
    )
    await db.commit()

    return ReviewActionResponse(
        success=True,
        message="Review action undone successfully",
        next_product_id=None,
    )


@router.get("/{client_id}/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewStatsResponse:
    """
    Get review statistics for a client.

    Returns counts for each review status.
    """
    # Validate client belongs to user
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

    # Count total generated products
    total_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.status == "generated",
        )
    )
    total_generated = total_result.scalar() or 0

    # Count pending review (review_status is null)
    pending_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
    )
    pending_review = pending_result.scalar() or 0

    # Count manually approved
    approved_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "approved",
        )
    )
    manually_approved = approved_result.scalar() or 0

    # Count manually rejected
    rejected_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "rejected",
        )
    )
    manually_rejected = rejected_result.scalar() or 0

    # Count AI approved
    ai_approved_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.ai_review_status == "ai_approved",
        )
    )
    ai_approved = ai_approved_result.scalar() or 0

    # Count AI rejected
    ai_rejected_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.ai_review_status == "ai_rejected",
        )
    )
    ai_rejected = ai_rejected_result.scalar() or 0

    # Count edited
    edited_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "edited",
        )
    )
    edited = edited_result.scalar() or 0

    return ReviewStatsResponse(
        total_generated=total_generated,
        pending_review=pending_review,
        manually_approved=manually_approved,
        manually_rejected=manually_rejected,
        ai_approved=ai_approved,
        ai_rejected=ai_rejected,
        edited=edited,
    )


@router.get("/{client_id}/next-unreviewed")
async def get_next_unreviewed(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get next unreviewed product for a client.

    Returns product_group_id or null if none remaining.
    """
    # Validate client belongs to user
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

    # Find next unreviewed product (row_index order)
    next_result = await db.execute(
        select(ProductGroup)
        .join(Product, Product.group_id == ProductGroup.id)
        .where(
            ProductGroup.client_id == client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
        .order_by(Product.row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return {"product_group_id": str(next_group.id) if next_group else None}
