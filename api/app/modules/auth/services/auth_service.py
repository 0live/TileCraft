import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.security import (
    get_token,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import Token
from app.modules.auth.services.google_auth import GoogleAuthService
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserRead


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repository: UserRepository, settings: Settings):
        self.user_repository = user_repository
        self.settings = settings

    async def register(self, user: UserCreate) -> UserRead:
        """Register a new user."""
        existing_email = await self.user_repository.session.exec(
            select(User).where(User.email == user.email)
        )
        if existing_email.first():
            raise HTTPException(status_code=400, detail="Email already registered")

        existing_username = await self.user_repository.get_by_username(user.username)
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_pw = hash_password(user.password)
        user_data = user.model_dump(exclude={"password", "roles", "teams"})
        user_data["hashed_password"] = hashed_pw
        user_data["roles"] = [UserRole.USER]

        new_user = await self.user_repository.create(user_data)
        return await self.user_repository.get_by_username(new_user.username)

    async def login(self, username: str, password: str) -> Token:
        """Authenticate user and return token."""
        user = await self.user_repository.get_by_username(username)
        if user and verify_password(password, user.hashed_password):
            return get_token(UserRead.model_validate(user), settings=self.settings)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    async def google_login(self, request: Request) -> dict:
        """Initiate Google OAuth flow."""
        return await GoogleAuthService.login(request)

    async def google_callback(self, request: Request) -> Token:
        """Handle Google OAuth callback."""
        user_info = await GoogleAuthService.callback(request)

        email = user_info.get("email")
        existing_user_result = await self.user_repository.session.exec(
            select(User).where(User.email == email)
        )
        existing_user = existing_user_result.first()

        if existing_user:
            return get_token(
                UserRead.model_validate(existing_user), settings=self.settings
            )

        # Create new user from Google info
        user_data = {
            "email": email,
            "username": user_info.get("name") or email.split("@")[0],
        }
        hashed_pw = hash_password(secrets.token_urlsafe(15))
        new_user = User(**user_data, roles=[UserRole.USER], hashed_password=hashed_pw)
        self.user_repository.session.add(new_user)
        await self.user_repository.session.commit()
        await self.user_repository.session.refresh(new_user)

        reloaded_user = await self.user_repository.get_by_username(new_user.username)
        return get_token(UserRead.model_validate(reloaded_user), settings=self.settings)


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    repo = UserRepository(session, User)
    return AuthService(repo, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
