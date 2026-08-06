import bcrypt

# Patch bcrypt.hashpw to truncate inputs > 72 bytes to fix passlib 1.7.4 + bcrypt 4.0+ compatibility
_orig_hashpw = bcrypt.hashpw

def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)

bcrypt.hashpw = _safe_hashpw

from passlib.context import CryptContext
from app.config import settings

# Create password context with bcrypt
pwd_context = CryptContext(

    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds
)


def hash_password(plain: str) -> str:
    """
    Hash a plain text password using bcrypt.
    """
    return pwd_context.hash(plain[:72])


# Alias for backward compatibility / tests
get_password_hash = hash_password



def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    """
    try:
        return pwd_context.verify(plain[:72], hashed)
    except Exception:
        return False

