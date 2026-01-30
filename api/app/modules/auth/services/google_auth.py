from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

from app.core.config import get_settings

# =============================================================================
# OAuth Configuration
# =============================================================================

settings = get_settings()
oauth = OAuth()

if settings.activate_google_auth:
    if not settings.google_client_id or not settings.google_client_secret:
        raise ValueError("Google SSO keys are missing")
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile", "response_type": "code"},
    )


class GoogleAuthService:
    @staticmethod
    async def login(request: Request) -> dict:
        """Initiate Google OAuth flow."""
        if not oauth.google:
            raise HTTPException(
                status_code=500, detail="Google OAuth configuration failed"
            )
        base_url = str(request.base_url).rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        redirect_uri = f"{base_url}/auth/google/callback"
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @staticmethod
    async def callback(request: Request) -> dict:
        """Handle Google OAuth callback and return user info."""
        if not oauth.google:
            raise HTTPException(
                status_code=502, detail="Google OAuth configuration failed"
            )

        auth_result = await oauth.google.authorize_access_token(request)
        user_info = auth_result.get("userinfo")
        if not user_info or not user_info.get("email"):
            raise HTTPException(
                status_code=502, detail="Google OAuth data parsing failed"
            )
        return user_info
