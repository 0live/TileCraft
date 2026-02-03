import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, Request, Response

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.exceptions import AuthenticationException
from app.core.security import get_token
from app.modules.auth.models import RefreshToken
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import AuthResponse
from app.modules.auth.services.email_service import EmailService
from app.modules.auth.services.google_auth import GoogleAuthService
from app.modules.users.schemas import UserCreate, UserDetail
from app.modules.users.service import UserService, UserServiceDep


class AuthService:
    """Service for authentication operations."""

    def __init__(
        self,
        repository: AuthRepository,
        user_service: UserService,
        settings: Settings,
    ):
        self.repository = repository
        self.user_service = user_service
        self.settings = settings

    def _hash_token(self, token: str) -> str:
        """Hash the refresh token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def _issue_tokens(self, user: UserDetail, response: Response) -> AuthResponse:
        """Helper to issue access/refresh tokens and set cookie."""
        access_token_obj = get_token(user, settings=self.settings)
        refresh_token_str = await self.create_refresh_token(user.id)

        self.set_refresh_cookie(response, refresh_token_str)

        return AuthResponse(
            access_token=access_token_obj.access_token,
            token_type=access_token_obj.token_type,
            refresh_token=refresh_token_str,
        )

    async def register(self, user: UserCreate) -> UserDetail:
        """Register a new user and send verification email."""
        verification_token = secrets.token_urlsafe(32)
        new_user = await self.user_service.create_user(
            user, is_verified=False, verification_token=verification_token
        )
        await EmailService.send_verification_email(user.email, verification_token)
        return new_user

    def set_refresh_cookie(self, response: Response, token: str) -> None:
        """Helper to set the refresh token cookie."""
        response.set_cookie(
            key="refresh_token",
            value=token,
            httponly=True,
            secure=False if self.settings.env == "dev" else True,
            samesite="lax" if self.settings.env == "dev" else "strict",
            max_age=self.settings.refresh_token_expire_days * 24 * 60 * 60,
        )

    async def create_refresh_token(self, user_id: int) -> str:
        """Generate, hash, and store a new refresh token."""
        token_str = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token_str)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.settings.refresh_token_expire_days
        )

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        await self.repository.create_refresh_token(refresh_token)
        return token_str

    async def login(
        self, username: str, password: str, response: Response
    ) -> AuthResponse:
        """Authenticate user and return access + refresh tokens."""
        user = await self.user_service.authenticate_user(username, password)

        user_detail = UserDetail.model_validate(user)
        return await self._issue_tokens(user_detail, response)

    async def refresh_access_token(
        self, refresh_token: Optional[str], response: Response
    ) -> AuthResponse:
        """Validate refresh token and rotate it."""
        if not refresh_token:
            response.delete_cookie("refresh_token")
            raise AuthenticationException(
                params={"detail": "auth.refresh_token_missing"}
            )

        token_hash = self._hash_token(refresh_token)
        stored_token = await self.repository.get_refresh_token_by_hash(token_hash)

        if not stored_token:
            response.delete_cookie("refresh_token")
            raise AuthenticationException(
                params={"detail": "auth.refresh_token_invalid"}
            )

        expires_at = stored_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            await self.repository.revoke_refresh_token(stored_token.id)
            response.delete_cookie("refresh_token")
            raise AuthenticationException(
                params={"detail": "auth.refresh_token_invalid"}
            )

        # Revoke old token (Rotation)
        await self.repository.revoke_refresh_token(stored_token.id)

        # Get user to issue new tokens
        user = await self.user_service.get_user_internal(stored_token.user_id)

        return await self._issue_tokens(user, response)

    async def logout(self, refresh_token: Optional[str], response: Response) -> None:
        """Revoke the refresh token and clear cookie."""
        if refresh_token:
            token_hash = self._hash_token(refresh_token)
            stored_token = await self.repository.get_refresh_token_by_hash(token_hash)
            if stored_token:
                await self.repository.revoke_refresh_token(stored_token.id)

        response.delete_cookie("refresh_token")

    async def verify_email(self, token: str) -> None:
        """Verify user email."""
        success = await self.user_service.verify_user(token)
        if not success:
            raise AuthenticationException(params={"detail": "auth.verification_failed"})

    async def google_login(self, request: Request) -> dict:
        """Initiate Google OAuth flow."""
        return await GoogleAuthService.login(request)

    async def google_callback(
        self, request: Request, response: Response
    ) -> AuthResponse:
        """Handle Google OAuth callback."""
        user_info = await GoogleAuthService.callback(request)

        user = await self.user_service.get_or_create_google_user(user_info)

        return await self._issue_tokens(user, response)


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_service(
    session: SessionDep, user_service: UserServiceDep, settings: SettingsDep
) -> AuthService:
    repo = AuthRepository(session, RefreshToken)
    return AuthService(repo, user_service, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
