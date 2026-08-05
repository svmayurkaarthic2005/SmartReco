"""JWT token creation and validation"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of data to encode in the token (usually user_id, email, role)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com", "role": "user"})
        >>> len(token) > 50
        True
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with token payload if valid, None if invalid or expired.
        Never raises exceptions - always returns None on any error.
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_access_token(token)
        >>> payload["sub"]
        'user@example.com'
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except Exception:
        # Return None on ANY error (JWTError, ValueError, etc.)
        # Never raise exceptions
        return None
