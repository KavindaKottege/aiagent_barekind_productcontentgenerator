"""Settings API endpoints for admin configuration."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.settings import AppSettings
from app.models.user import User
from app.schemas.settings import (
    GenerationSettingsResponse,
    GenerationSettingsUpdate,
    HasApiKeyResponse,
    SettingsResponse,
    SettingsUpdate,
    TaskSettingsResponse,
    TaskSettingsUpdate,
)
from app.utils.dependencies import get_current_admin, get_current_user

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
        default_task3_prompt=settings.default_task3_prompt,
        default_task4_prompt=settings.default_task4_prompt,
        ai_model=settings.ai_model,
        ai_temperature=settings.ai_temperature,
        generation_soft_cap=settings.generation_soft_cap,
        task1_default_attributes=settings.task1_default_attributes,
        task1_mandatory_attributes=settings.task1_mandatory_attributes,
        task2_default_attributes=settings.task2_default_attributes,
        task2_mandatory_attributes=settings.task2_mandatory_attributes,
        task3_default_attributes=settings.task3_default_attributes,
        task3_mandatory_attributes=settings.task3_mandatory_attributes,
        task4_default_attributes=settings.task4_default_attributes,
        task4_mandatory_attributes=settings.task4_mandatory_attributes,
        task1_min_length=settings.task1_min_length,
        task1_max_length=settings.task1_max_length,
        task1_target_length=settings.task1_target_length,
        task2_min_length=settings.task2_min_length,
        task2_max_length=settings.task2_max_length,
        task2_target_length=settings.task2_target_length,
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
    if settings_update.default_task3_prompt is not None:
        settings.default_task3_prompt = settings_update.default_task3_prompt if settings_update.default_task3_prompt != "" else None
    if settings_update.default_task4_prompt is not None:
        settings.default_task4_prompt = settings_update.default_task4_prompt if settings_update.default_task4_prompt != "" else None

    # Update attribute settings if provided
    if settings_update.task1_default_attributes is not None:
        settings.task1_default_attributes = settings_update.task1_default_attributes
    if settings_update.task1_mandatory_attributes is not None:
        settings.task1_mandatory_attributes = settings_update.task1_mandatory_attributes
    if settings_update.task2_default_attributes is not None:
        settings.task2_default_attributes = settings_update.task2_default_attributes
    if settings_update.task2_mandatory_attributes is not None:
        settings.task2_mandatory_attributes = settings_update.task2_mandatory_attributes
    if settings_update.task3_default_attributes is not None:
        settings.task3_default_attributes = settings_update.task3_default_attributes
    if settings_update.task3_mandatory_attributes is not None:
        settings.task3_mandatory_attributes = settings_update.task3_mandatory_attributes
    if settings_update.task4_default_attributes is not None:
        settings.task4_default_attributes = settings_update.task4_default_attributes
    if settings_update.task4_mandatory_attributes is not None:
        settings.task4_mandatory_attributes = settings_update.task4_mandatory_attributes

    # Update length settings if provided
    if settings_update.task1_min_length is not None:
        settings.task1_min_length = settings_update.task1_min_length
    if settings_update.task1_max_length is not None:
        settings.task1_max_length = settings_update.task1_max_length
    if settings_update.task1_target_length is not None:
        settings.task1_target_length = settings_update.task1_target_length
    if settings_update.task2_min_length is not None:
        settings.task2_min_length = settings_update.task2_min_length
    if settings_update.task2_max_length is not None:
        settings.task2_max_length = settings_update.task2_max_length
    if settings_update.task2_target_length is not None:
        settings.task2_target_length = settings_update.task2_target_length

    await db.commit()
    await db.refresh(settings)

    return SettingsResponse(
        openai_api_key=settings.openai_api_key,
        has_api_key=settings.openai_api_key is not None and settings.openai_api_key != "",
        default_system_prompt=settings.default_system_prompt,
        default_task1_prompt=settings.default_task1_prompt,
        default_task2_prompt=settings.default_task2_prompt,
        default_task3_prompt=settings.default_task3_prompt,
        default_task4_prompt=settings.default_task4_prompt,
        ai_model=settings.ai_model,
        ai_temperature=settings.ai_temperature,
        generation_soft_cap=settings.generation_soft_cap,
        task1_default_attributes=settings.task1_default_attributes,
        task1_mandatory_attributes=settings.task1_mandatory_attributes,
        task2_default_attributes=settings.task2_default_attributes,
        task2_mandatory_attributes=settings.task2_mandatory_attributes,
        task3_default_attributes=settings.task3_default_attributes,
        task3_mandatory_attributes=settings.task3_mandatory_attributes,
        task4_default_attributes=settings.task4_default_attributes,
        task4_mandatory_attributes=settings.task4_mandatory_attributes,
        task1_min_length=settings.task1_min_length,
        task1_max_length=settings.task1_max_length,
        task1_target_length=settings.task1_target_length,
        task2_min_length=settings.task2_min_length,
        task2_max_length=settings.task2_max_length,
        task2_target_length=settings.task2_target_length,
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


@router.get("/generation", response_model=GenerationSettingsResponse)
async def get_generation_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> GenerationSettingsResponse:
    """
    Get generation-specific settings. Requires authentication.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        GenerationSettingsResponse with current generation configuration
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

    return GenerationSettingsResponse.model_validate(settings)


@router.patch("/generation", response_model=GenerationSettingsResponse)
async def update_generation_settings(
    updates: GenerationSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_db),
) -> GenerationSettingsResponse:
    """
    Update generation settings. Admin only.

    Args:
        updates: Generation settings updates
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated GenerationSettingsResponse
    """
    # Get settings row (id=1)
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    # If settings row doesn't exist, create it
    if settings is None:
        settings = AppSettings(id=1)
        db.add(settings)

    # Apply updates (only non-None values)
    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return GenerationSettingsResponse.model_validate(settings)


@router.get("/tasks", response_model=TaskSettingsResponse)
async def get_task_settings(
    current_user: Annotated[User, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_db),
) -> TaskSettingsResponse:
    """
    Get AI task settings. Admin only.

    Args:
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        TaskSettingsResponse with current task configuration
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

    return TaskSettingsResponse.model_validate(settings)


@router.patch("/tasks", response_model=TaskSettingsResponse)
async def update_task_settings(
    updates: TaskSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: AsyncSession = Depends(get_db),
) -> TaskSettingsResponse:
    """
    Update AI task settings. Admin only.

    Args:
        updates: Task settings updates
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated TaskSettingsResponse
    """
    # Get settings row (id=1)
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    # If settings row doesn't exist, create it
    if settings is None:
        settings = AppSettings(id=1)
        db.add(settings)

    # Apply updates (only non-None values)
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            # Handle empty strings for prompts -> None
            if field.endswith('_prompt') and value == "":
                setattr(settings, field, None)
            else:
                setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return TaskSettingsResponse.model_validate(settings)
