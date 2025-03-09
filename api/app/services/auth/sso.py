import os
from authlib.integrations.starlette_client import OAuth

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
