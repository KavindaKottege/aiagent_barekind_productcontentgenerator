"""Client API endpoints for brand profile management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientPublic, ClientUpdate
from app.utils.dependencies import get_current_admin, get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientPublic])
async def list_clients(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[ClientPublic]:
    """List all clients for current user."""
    result = await db.execute(
        select(Client).where(Client.user_id == current_user.id).order_by(Client.brand_name)
    )
    clients = result.scalars().all()
    return [ClientPublic.from_orm_with_computed(c) for c in clients]


@router.post("/", response_model=ClientPublic, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ClientPublic:
    """Create new client profile."""
    db_client = Client(**client_data.model_dump(), user_id=current_user.id)
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return ClientPublic.from_orm_with_computed(db_client)


@router.get("/{client_id}", response_model=ClientPublic)
async def get_client(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ClientPublic:
    """Get single client by ID."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientPublic.from_orm_with_computed(client)


@router.patch("/{client_id}", response_model=ClientPublic)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ClientPublic:
    """Update client profile. Users can only update their own clients."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == current_user.id)
    )
    db_client = result.scalar_one_or_none()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Only update fields that were provided (exclude_unset)
    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_client, field, value)

    await db.commit()
    await db.refresh(db_client)
    return ClientPublic.from_orm_with_computed(db_client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    admin: Annotated[User, Depends(get_current_admin)],  # Admin only
    db: AsyncSession = Depends(get_db),
):
    """Delete client profile. Admin only."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    db_client = result.scalar_one_or_none()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    await db.delete(db_client)
    await db.commit()
