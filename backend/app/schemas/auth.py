"""Authentication request/response schemas"""

import re
import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import UserRole


class RegisterRequest(BaseModel):
    """User registration request schema"""
    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    
    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password complexity using regex.
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one digit
        - At least one special character (@$!%*?&)
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Production regex: ^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$
        # Must contain uppercase, digit, and special character from [@$!%*?&]
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', v):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one digit, and one special character (@$!%*?&)"
            )
        
        return v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not just whitespace"""
        if not v or v.strip() == "":
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "password": "SecurePass123!"
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "john.doe@example.com",
                    "password": "SecurePass123!"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Authentication token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID (UUID as string)")
    role: str = Field(..., description="User role (user/admin)")
    name: str = Field(..., description="User's full name")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "role": "user",
                    "name": "John Doe",
                    "email": "john.doe@example.com"
                }
            ]
        }
    }


class UserProfile(BaseModel):
    """User profile schema for /auth/me endpoint"""
    id: str  # UUID as string for JSON serialization
    name: str
    email: str
    role: str  # UserRole enum value as string
    created_at: str  # ISO format datetime string
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "role": "user",
                    "created_at": "2026-08-04T10:30:00"
                }
            ]
        }
    }


# Alias for backward compatibility
UserProfileResponse = UserProfile


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str = Field(..., description="Error message")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": "Invalid credentials"
                }
            ]
        }
    }
