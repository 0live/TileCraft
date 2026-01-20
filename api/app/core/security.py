from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings
from app.modules.auth.schemas import Token
from app.modules.users.schemas import UserRead


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    data: dict,
    settings: Settings,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, str(settings.private_key), algorithm=settings.algorithm
    )


def decode_token(token: str, settings: Settings) -> dict:
    """Decode a JWT token."""
    return jwt.decode(token, str(settings.private_key), algorithms=[settings.algorithm])


# =============================================================================
# OAuth2 Scheme
# =============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_token(user: UserRead, settings: Settings) -> Token:
    """Generate a Token response for a user."""
    token = create_access_token(data={**user.model_dump()}, settings=settings)
    return Token(access_token=token, token_type="bearer")
