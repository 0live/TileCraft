from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.db.users import User
from app.services.users import (
    authenticate_user,
    create_user,
    get_current_user,
    update_user,
)
from app.core.database import SessionDep
from app.models.users import UserRead, UserCreate, UserUpdate
from app.models.auth import Token

userRouter = APIRouter(prefix="/users", tags=["Users"])


@userRouter.post("/register", response_model=UserRead)
def register(user: UserCreate, session: SessionDep):
    return create_user(user, session)


@userRouter.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
):
    return authenticate_user(session, form_data.username, form_data.password)


@userRouter.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@userRouter.patch("/{user_id}", response_model=UserRead)
def patch_user(
    user_id: int,
    user: UserUpdate,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return update_user(user_id, user, session, current_user)
