from authlib.integrations.starlette_client import OAuth
from fastapi import Request

from app.core.config import Settings
from app.core.exceptions import (
    ExternalServiceException,
    PermissionDeniedException,
    SecurityException,
)

# =============================================================================
# OAuth Configuration
# =============================================================================


class GoogleAuthService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.oauth = OAuth()

        if self.settings.activate_google_auth:
            if (
                not self.settings.google_client_id
                or not self.settings.google_client_secret
            ):
                raise SecurityException(key="auth.google_keys_missing")

            self.oauth.register(
                name="google",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={
                    "scope": "openid email profile",
                    "response_type": "code",
                },
            )

    async def login(self, request: Request) -> dict:
        """Initiate Google OAuth flow."""
        self._validate_config()
        if not self.oauth.google:
            raise SecurityException(key="auth.google_config_error")

        base_url = str(request.base_url).rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        redirect_uri = f"{base_url}/auth/google/callback"
        return await self.oauth.google.authorize_redirect(request, redirect_uri)

    async def callback(self, request: Request) -> dict:
        """Handle Google OAuth callback and return user info."""
        self._validate_config()
        if not self.oauth.google:
            raise SecurityException(key="auth.google_config_error")

        auth_result = await self.oauth.google.authorize_access_token(request)
        user_info = auth_result.get("userinfo")
        if not user_info or not user_info.get("email"):
            raise ExternalServiceException(key="auth.google_validation_failed")
        return user_info

    def _validate_config(self):
        """Validate Google Auth configuration and permissions."""
        if not self.settings.activate_google_auth:
            raise PermissionDeniedException(key="auth.google_disabled")
        if not self.settings.allow_self_registration:
            raise PermissionDeniedException(key="auth.registration_disabled")
