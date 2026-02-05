from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.core.messages import MessageService
from app.core.rate_limit import limiter
from app.modules.auth.schemas import Token
from app.modules.auth.services.auth_service import AuthServiceDep
from app.modules.users.schemas import UserCreate, UserDetail

authRouter = APIRouter(prefix="/auth", tags=["Auth"])


@authRouter.post("/register", response_model=UserDetail)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate, service: AuthServiceDep):
    """Register a new user."""
    return await service.register(user)


@authRouter.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
    response: Response,
):
    """Login with username and password."""
    return await service.login(form_data.username, form_data.password, response)


@authRouter.post("/refresh", response_model=Token)
async def refresh_token(
    service: AuthServiceDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    """Refresh access token using http-only cookie."""
    return await service.refresh_access_token(refresh_token, response)


@authRouter.post("/logout")
async def logout(
    service: AuthServiceDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    """Logout and revoke refresh token."""
    await service.logout(refresh_token, response)
    return {"message": MessageService.get_message("auth.logout_success")}


@authRouter.get("/verify")
async def verify_email(token: str, service: AuthServiceDep):
    """Verify user account via email token."""
    await service.verify_email(token)
    return {"message": MessageService.get_message("auth.verification_success")}


@authRouter.get("/google")
async def login_google(request: Request, service: AuthServiceDep):
    """Initiate Google OAuth login."""
    return await service.google_login(request)


@authRouter.get("/google/callback", response_model=Token)
async def google_callback(
    request: Request,
    service: AuthServiceDep,
    response: Response,
):
    """Handle Google OAuth callback."""
    """Handle Google OAuth callback."""
    return await service.google_callback(request, response)
