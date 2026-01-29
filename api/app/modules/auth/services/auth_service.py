import secrets
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.security import get_token
from app.modules.auth.schemas import Token
from app.modules.auth.services.google_auth import GoogleAuthService
from app.modules.users.schemas import UserCreate, UserDetail
from app.modules.users.service import UserService, UserServiceDep


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_service: UserService, settings: Settings):
        self.user_service = user_service
        self.settings = settings

    async def register(self, user: UserCreate) -> UserDetail:
        """Register a new user."""
        return await self.user_service.create_user(user)

    async def login(self, username: str, password: str) -> Token:
        """Authenticate user and return token."""
        return await self.user_service.authenticate_user(username, password)

    async def google_login(self, request: Request) -> dict:
        """Initiate Google OAuth flow."""
        return await GoogleAuthService.login(request)

    async def google_callback(self, request: Request) -> Token:
        """Handle Google OAuth callback."""
        user_info = await GoogleAuthService.callback(request)

        email = user_info.get("email")
        existing_user = await self.user_service.get_by_email(email)

        if existing_user:
            return get_token(
                UserDetail.model_validate(existing_user), settings=self.settings
            )

        # Prepare OAuth user data, delegate creation to UserService
        username = user_info.get("name") or email.split("@")[0]
        user_create = UserCreate(
            email=email,
            username=username,
            password=secrets.token_urlsafe(15),
        )
        new_user = await self.user_service.create_user(user_create)
        return get_token(new_user, settings=self.settings)


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_service(
    user_service: UserServiceDep, settings: SettingsDep
) -> AuthService:
    return AuthService(user_service, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
