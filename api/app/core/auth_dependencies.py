from typing import Annotated

from fastapi import Depends
from jwt.exceptions import InvalidTokenError

from app.core.exceptions import AuthenticationException
from app.core.security import decode_token, oauth2_scheme
from app.modules.users.schemas import UserRead
from app.modules.users.service import UserServiceDep


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: UserServiceDep,
) -> UserRead:
    """Get current authenticated user from token."""
    try:
        payload = decode_token(token, settings=service.settings)
        username = payload.get("username")
        if username is None:
            raise AuthenticationException(params={"detail": "auth.invalid_credentials"})
    except InvalidTokenError:
        raise AuthenticationException(params={"detail": "auth.invalid_credentials"})

    user = await service.get_by_username(username)
    if user is None:
        raise AuthenticationException(params={"detail": "auth.user_not_found"})
    return UserRead.model_validate(user)
