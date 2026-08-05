"""Authentication dependencies for FastAPI routes"""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.database import get_db
from app.models import User, UserRole


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User ORM object
        
    Raises:
        HTTPException 401: If token is invalid or user not found
        
    Example:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Query database for user
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    except ValueError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (placeholder for future is_active field).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User ORM object if active
        
    Raises:
        HTTPException 400: If user is inactive
    """
    # Placeholder: Add is_active field to User model if needed
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require that the current user has admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User ORM object if admin
        
    Raises:
        HTTPException 403: If user is not an admin
        
    Example:
        @app.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            admin: User = Depends(require_admin)
        ):
            # Only admins can access this
            pass
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user


# Optional: Helper for checking specific roles
def require_role(*allowed_roles: UserRole):
    """
    Factory function to create a dependency that checks for specific roles.
    
    Args:
        *allowed_roles: One or more UserRole values
        
    Returns:
        Dependency function
        
    Example:
        @app.get("/admin-or-moderator")
        async def route(user: User = Depends(require_role(UserRole.ADMIN))):
            pass
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user
    return role_checker


# Alias for backward compatibility
get_current_admin_user = require_admin

