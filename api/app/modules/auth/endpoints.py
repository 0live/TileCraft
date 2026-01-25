from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.auth.schemas import Token
from app.modules.auth.services.auth_service import AuthServiceDep
from app.modules.users.schemas import UserCreate, UserDetail

authRouter = APIRouter(prefix="/auth", tags=["Auth"])


@authRouter.post("/register", response_model=UserDetail)
async def register(user: UserCreate, service: AuthServiceDep):
    """Register a new user."""
    return await service.register(user)


@authRouter.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    """Login with username and password."""
    return await service.login(form_data.username, form_data.password)


@authRouter.get("/google")
async def login_google(request: Request, service: AuthServiceDep):
    """Initiate Google OAuth login."""
    return await service.google_login(request)


@authRouter.get("/google/callback", response_model=Token)
async def google_callback(request: Request, service: AuthServiceDep):
    """Handle Google OAuth callback."""
    return await service.google_callback(request)
