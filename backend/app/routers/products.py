"""Product API endpoints for Excel upload and product management."""
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4
import shutil
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query, status
from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.user import User
from app.schemas.product import UploadResponse, ProductGroupPublic, ProductGroupWithVariants, ProductPublic
from app.services import ExcelParser, ExactColumnMapper, VariantGrouper
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/upload", response_model=UploadResponse)
async def upload_products(
    file: UploadFile,
    client_id: Annotated[UUID, Query(description="Client ID to associate products with")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """
    Upload Excel file with product data.

    - Parses Excel in streaming mode (memory efficient)
    - Maps columns using exact 1:1 matching (Faire template format)
    - Groups variants by Name/Token/SKU
    - Replaces existing products for this client
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported"
        )

    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        tmp_path = Path(tmp.name)
        shutil.copyfileobj(file.file, tmp)

    # Also save a permanent copy for export (preserves formatting, extra sheets, etc.)
    uploads_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    permanent_path = uploads_dir / f"{client_id}.xlsx"
    shutil.copy2(str(tmp_path), str(permanent_path))

    parser = ExcelParser(tmp_path)
    mapper = ExactColumnMapper()
    grouper = VariantGrouper()

    try:
        # Parse Excel in batches
        all_products = []
        headers = None

        for batch in parser.parse():
            if headers is None and batch:
                headers = list(batch[0].keys())
            all_products.extend(batch)

        if not all_products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel file is empty or has no data rows"
            )

        # Map columns
        mapping_result = mapper.map_columns(headers)

        if mapping_result['missing_required']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(mapping_result['missing_required'])}. "
                       f"Found columns: {', '.join(headers)}"
            )

        # Apply mapping
        mapped_products = mapper.apply_mapping(all_products, mapping_result['mapped'])

        # Add row indices for export ordering
        for i, product in enumerate(mapped_products):
            product['row_index'] = i + 2  # +2 because row 1 is header

        # Group variants
        groups, products_with_groups = grouper.group_variants(mapped_products)

        # Persist original column order on the client for export reconstruction
        client_result = await db.execute(
            select(Client).where(Client.id == client_id, Client.user_id == current_user.id)
        )
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        client.excel_column_order = headers

        # Delete existing products and groups for this client
        await db.execute(
            delete(Product).where(Product.client_id == client_id)
        )
        await db.execute(
            delete(ProductGroup).where(ProductGroup.client_id == client_id)
        )

        # Bulk insert groups first
        group_id_map = {}  # group_idx -> actual UUID
        group_records = []
        for group in groups:
            group_id = uuid4()
            group_id_map[group['group_idx']] = group_id
            group_records.append({
                'id': group_id,
                'client_id': client_id,
                'user_id': current_user.id,
                'product_name': group['product_name'],
                'product_token': group['product_token'],
                'sku': group['sku'],
                'variant_count': group['variant_count'],
                'first_row_index': group.get('first_row_index', 0),
                'status': 'pending',
            })

        if group_records:
            await db.execute(insert(ProductGroup), group_records)

        # Bulk insert products
        product_records = []
        for product in products_with_groups:
            group_idx = product.pop('_group_idx')
            product_records.append({
                'id': uuid4(),
                'client_id': client_id,
                'user_id': current_user.id,
                'group_id': group_id_map[group_idx],
                **{k: v for k, v in product.items() if k in Product.__table__.columns.keys()},
                'unmapped_data': product.get('unmapped_data', {}),
            })

        if product_records:
            await db.execute(insert(Product), product_records)

        await db.commit()

        # Calculate stats
        variant_groups = sum(1 for g in groups if g['variant_count'] > 1)
        standalone = len(groups) - variant_groups

        return UploadResponse(
            total_rows=len(all_products),
            product_groups=len(groups),
            variant_groups=variant_groups,
            standalone_products=standalone,
            mapped_columns=mapping_result['mapped'],
            unmapped_columns=mapping_result['unmapped'],
        )

    finally:
        parser.close()
        tmp_path.unlink(missing_ok=True)
        await file.close()


@router.get("/groups", response_model=list[ProductGroupPublic])
async def list_product_groups(
    client_id: Annotated[UUID, Query(description="Client ID to filter products")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[ProductGroupPublic]:
    """List all product groups for a client."""
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == client_id, ProductGroup.user_id == current_user.id)
        .order_by(ProductGroup.first_row_index)
    )
    groups = result.scalars().all()
    return [ProductGroupPublic.model_validate(g) for g in groups]


@router.get("/groups/{group_id}", response_model=ProductGroupWithVariants)
async def get_product_group_with_variants(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ProductGroupWithVariants:
    """Get a product group with all its variant products."""
    # Get group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == group_id, ProductGroup.user_id == current_user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Product group not found")

    # Get variants
    result = await db.execute(
        select(Product)
        .where(Product.group_id == group_id)
        .order_by(Product.row_index)
    )
    variants = result.scalars().all()

    return ProductGroupWithVariants(
        **ProductGroupPublic.model_validate(group).model_dump(),
        variants=[ProductPublic.model_validate(v) for v in variants]
    )


@router.delete("/client/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_products(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Delete all products and groups for a client."""
    # Verify user owns products (via client ownership - enforced by FK)
    await db.execute(
        delete(Product).where(Product.client_id == client_id, Product.user_id == current_user.id)
    )
    await db.execute(
        delete(ProductGroup).where(ProductGroup.client_id == client_id, ProductGroup.user_id == current_user.id)
    )
    await db.commit()
