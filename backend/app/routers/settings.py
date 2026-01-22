"""Settings API endpoints for admin configuration."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.settings import AppSettings
from app.models.user import User
from app.schemas.settings import HasApiKeyResponse, SettingsResponse, SettingsUpdate
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    current_user: Annotated[User, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """
    Get application settings (admin only).

    Args:
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        SettingsResponse with current configuration
    """
    # Get settings row (id=1)
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    # If settings row doesn't exist, create it
    if settings is None:
        settings = AppSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return SettingsResponse(
        openai_api_key=settings.openai_api_key,
        has_api_key=settings.openai_api_key is not None and settings.openai_api_key != "",
        default_system_prompt=settings.default_system_prompt,
        default_task1_prompt=settings.default_task1_prompt,
        default_task2_prompt=settings.default_task2_prompt,
    )


@router.put("/", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """
    Update application settings (admin only).

    Args:
        settings_update: New settings values
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated SettingsResponse
    """
    # Get settings row (id=1)
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    # If settings row doesn't exist, create it
    if settings is None:
        settings = AppSettings(id=1)
        db.add(settings)

    # Update API key if provided
    if settings_update.openai_api_key is not None:
        settings.openai_api_key = settings_update.openai_api_key

    # Update prompt fields if provided (allow clearing with empty string -> None)
    if settings_update.default_system_prompt is not None:
        settings.default_system_prompt = settings_update.default_system_prompt if settings_update.default_system_prompt != "" else None
    if settings_update.default_task1_prompt is not None:
        settings.default_task1_prompt = settings_update.default_task1_prompt if settings_update.default_task1_prompt != "" else None
    if settings_update.default_task2_prompt is not None:
        settings.default_task2_prompt = settings_update.default_task2_prompt if settings_update.default_task2_prompt != "" else None

    await db.commit()
    await db.refresh(settings)

    return SettingsResponse(
        openai_api_key=settings.openai_api_key,
        has_api_key=settings.openai_api_key is not None and settings.openai_api_key != "",
        default_system_prompt=settings.default_system_prompt,
        default_task1_prompt=settings.default_task1_prompt,
        default_task2_prompt=settings.default_task2_prompt,
    )


@router.get("/has-api-key", response_model=HasApiKeyResponse)
async def has_api_key(
    db: AsyncSession = Depends(get_db),
) -> HasApiKeyResponse:
    """
    Check if OpenAI API key is configured (public endpoint).

    This is used by the frontend to determine if initial setup is needed.

    Args:
        db: Database session

    Returns:
        HasApiKeyResponse indicating if API key is configured
    """
    # Get settings row (id=1)
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    # If settings row doesn't exist, API key is not configured
    if settings is None:
        return HasApiKeyResponse(has_api_key=False)

    return HasApiKeyResponse(
        has_api_key=settings.openai_api_key is not None and settings.openai_api_key != ""
    )
