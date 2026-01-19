import os

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

# =============================================================================
# OAuth Configuration
# =============================================================================

ACTIVATE_GOOGLE_SSO = os.getenv("ACTIVATE_GOOGLE_SSO", "false").lower() == "true"

oauth = OAuth()

if ACTIVATE_GOOGLE_SSO:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google SSO keys are missing")
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
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
