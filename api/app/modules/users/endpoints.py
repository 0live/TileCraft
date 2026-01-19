from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.database import SessionDep
from app.modules.teams.models import Team
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import UserRead, UserUpdate
from app.modules.users.service import UserServiceDep, get_current_user

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


@userRouter.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: int,
    user: UserUpdate,
    service: UserServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.update_user(user_id, user, current_user)
