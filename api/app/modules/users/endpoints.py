from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.modules.users.models import User, UserRole
from app.modules.users.schemas import UserRead, UserUpdate
from app.modules.users.service import UserServiceDep, get_current_user

userRouter = APIRouter(prefix="/users", tags=["Users"])


@userRouter.get("", response_model=List[UserRead])
async def get_all_users(
    service: UserServiceDep, current_user: UserRead = Depends(get_current_user)
):
    if UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be an admin"
        )
    return await service.get_all_users()


@userRouter.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@userRouter.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    if UserRole.ADMIN not in current_user.roles and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be an admin"
        )
    return await service.get_user_by_id(user_id)


@userRouter.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: int,
    user: UserUpdate,
    service: UserServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.update_user(user_id, user, current_user)


@userRouter.delete("/{user_id}")
async def delete_user(
    user_id: int,
    service: UserServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    if UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be an admin"
        )
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
