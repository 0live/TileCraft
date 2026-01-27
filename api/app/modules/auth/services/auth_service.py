import secrets
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.exceptions import AuthenticationException
from app.core.security import get_token, hash_password, verify_password
from app.modules.auth.schemas import Token
from app.modules.auth.services.google_auth import GoogleAuthService
from app.modules.teams.models import Team
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserDetail


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repository: UserRepository, settings: Settings):
        self.user_repository = user_repository
        self.settings = settings

    async def register(self, user: UserCreate) -> UserDetail:
        """Register a new user."""
        # Validate unique credentials using centralized method
        await self.user_repository.validate_unique_credentials(
            user.email, user.username
        )

        # Create user
        hashed_pw = hash_password(user.password)
        user_data = user.model_dump(exclude={"password", "roles", "teams"})
        user_data["hashed_password"] = hashed_pw
        user_data["roles"] = [UserRole.USER]

        new_user = await self.user_repository.create(user_data)
        await self.user_repository.session.commit()

        return await self.user_repository.get(
            new_user.id, options=[selectinload(User.teams).selectinload(Team.users)]
        )

    async def login(self, username: str, password: str) -> Token:
        """Authenticate user and return token."""
        user = await self.user_repository.get_by_username(
            username, options=[selectinload(User.teams).selectinload(Team.users)]
        )
        if user and verify_password(password, user.hashed_password):
            return get_token(UserDetail.model_validate(user), settings=self.settings)
        raise AuthenticationException()

    async def google_login(self, request: Request) -> dict:
        """Initiate Google OAuth flow."""
        return await GoogleAuthService.login(request)

    async def google_callback(self, request: Request) -> Token:
        """Handle Google OAuth callback."""
        user_info = await GoogleAuthService.callback(request)

        email = user_info.get("email")
        existing_user = await self.user_repository.get_by_email(email)

        if existing_user:
            return get_token(
                UserDetail.model_validate(existing_user), settings=self.settings
            )

        # Create new user from Google OAuth
        username = user_info.get("name") or email.split("@")[0]

        # Validate unique credentials
        await self.user_repository.validate_unique_credentials(email, username)

        # Create user
        hashed_pw = hash_password(secrets.token_urlsafe(15))
        user_data = {
            "email": email,
            "username": username,
            "hashed_password": hashed_pw,
            "roles": [UserRole.USER],
        }

        new_user = await self.user_repository.create(user_data)
        await self.user_repository.session.commit()

        user_detail = await self.user_repository.get(
            new_user.id, options=[selectinload(User.teams).selectinload(Team.users)]
        )

        return get_token(user_detail, settings=self.settings)


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    user_repo = UserRepository(session, User)
    return AuthService(user_repo, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
