from fastapi import APIRouter, HTTPException, Request
from app.services.users import manage_google_user
from app.core.database import SessionDep
from api.app.services.auth.sso import oauth


googleRouter = APIRouter(prefix="/google", tags=["Google SSO"])


@googleRouter.get("")
async def login_google(request: Request):
    if not oauth.google:
        raise HTTPException(status_code=500, detail="Google OAuth configuration failed")
    base_url = str(request.base_url).rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        base_url = "http://" + base_url

    redirect_uri = f"{base_url}/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@googleRouter.get("/callback")
async def auth_google_callback(request: Request, session: SessionDep):
    return await manage_google_user(request, session)
