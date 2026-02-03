from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings
from app.core.exceptions import AuthenticationException
from app.modules.auth.schemas import Token
from app.modules.users.schemas import UserDetail
from app.modules.users.service import UserServiceDep


def create_access_token(
    data: dict,
    settings: Settings,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
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


def get_token(user: UserDetail, settings: Settings) -> Token:
    """Generate a Token response for a user."""
    token = create_access_token(data={**user.model_dump()}, settings=settings)
    return Token(access_token=token, token_type="bearer")


# =============================================================================
# Auth Dependencies
# =============================================================================


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: UserServiceDep,
) -> UserDetail:
    """Get current authenticated user from token."""
    try:
        payload = decode_token(token, settings=service.settings)
        username = payload.get("username")
        if username is None:
            raise AuthenticationException(params={"detail": "auth.invalid_credentials"})
    except InvalidTokenError:
        raise AuthenticationException(params={"detail": "auth.invalid_credentials"})

    user = await service.get_by_username(username, with_relations=True)
    if user is None:
        raise AuthenticationException(params={"detail": "auth.user_not_found"})
    return UserDetail.model_validate(user)
