"""Authentication and authorization"""

from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_access_token
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_role,
    oauth2_scheme
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "require_role",
    "oauth2_scheme",
]
