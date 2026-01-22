"""Authentication routes for signup, login, and user management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.utils.auth import create_access_token, hash_password, verify_password
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Register a new user.

    First user automatically becomes admin.

    Args:
        user_data: User registration data (email, name, password)
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if this is the first user (becomes admin)
    count_result = await db.execute(select(func.count()).select_from(User))
    user_count = count_result.scalar()
    is_first_user = user_count == 0

    # Create new user
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_pwd,
        is_admin=is_first_user,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Log user creation
    logger.info(
        f"User created: email={new_user.email}, is_admin={new_user.is_admin}, id={new_user.id}"
    )

    # Create access token
    access_token = create_access_token({"user_id": str(new_user.id)})

    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate user and return JWT token.

    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Find user by email (form.username is email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token({"user_id": str(user.id)})

    logger.info(f"User logged in: email={user.email}, id={user.id}")

    return Token(access_token=access_token)


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """
    Logout current user.

    Note: Actual token invalidation handled client-side by deleting the token.
    Server-side token blacklisting would require Redis or similar.

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: email={current_user.email}, id={current_user.id}")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current authenticated user information.

    Args:
        current_user: Authenticated user from token

    Returns:
        User data
    """
    return current_user
