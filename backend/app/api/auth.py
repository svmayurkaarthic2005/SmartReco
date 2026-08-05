"""Authentication API routes"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.database import get_db
from app.models import User, UserRole
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserProfile,
    ErrorResponse
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Email already registered"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    },
    summary="Register a new user",
    description="Create a new user account with name, email, and password. Password must meet complexity requirements."
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Register a new user account.
    
    Password Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns JWT access token upon successful registration.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create new user
    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=password_hash,
        role=UserRole.USER,  # Default role
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role.value
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(new_user.id),
        role=new_user.role.value,
        name=new_user.name
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    },
    summary="Login user",
    description="Authenticate user with email and password. Returns JWT access token."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.
    
    The token should be included in subsequent requests in the Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        role=user.role.value,
        name=user.name
    )


@router.get(
    "/me",
    response_model=UserProfile,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"model": ErrorResponse, "description": "Invalid token"}
    },
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user."
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """
    Get current user profile.
    
    Requires valid JWT token in Authorization header.
    """
    return UserProfile(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
        created_at=current_user.created_at.isoformat()
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    },
    summary="Refresh access token",
    description="Get a new access token using current valid token."
)
async def refresh_token(
    current_user: User = Depends(get_current_user)
) -> TokenResponse:
    """
    Refresh the access token.
    
    Returns a new JWT token with extended expiration.
    """
    # Create new access token
    access_token = create_access_token(
        data={
            "sub": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role.value
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(current_user.id),
        role=current_user.role.value,
        name=current_user.name
    )
