from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.db.teams import Team
from app.db.users import User
from app.models.auth import Token
from app.models.user_roles import UserRole
from app.models.users import UserCreate, UserRead, UserUpdate
from app.services.users import (
    authenticate_user,
    create_user,
    get_current_user,
    update_user,
)

userRouter = APIRouter(prefix="/users", tags=["Users"])


@userRouter.get("", response_model=List[UserRead])
async def get_all_users(
    session: SessionDep, current_user: UserRead = Depends(get_current_user)
):
    if UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be an admin"
        )
    result = await session.exec(
        select(User).options(selectinload(User.teams).selectinload(Team.users))
    )
    return result.all()


@userRouter.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@userRouter.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    if UserRole.ADMIN not in current_user.roles and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be an admin"
        )
    result = await session.exec(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.teams).selectinload(Team.users))
    )
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@userRouter.post("/register", response_model=UserRead)
async def register(user: UserCreate, session: SessionDep):
    return await create_user(user, session)


@userRouter.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    settings: Annotated[Settings, Depends(get_settings)],
):
    return await authenticate_user(
        session, form_data.username, form_data.password, settings
    )


@userRouter.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: int,
    user: UserUpdate,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await update_user(user_id, user, session, current_user)
