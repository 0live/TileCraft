from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.modules.maps.schemas import MapCreate, MapRead, MapUpdate
from app.modules.maps.service import MapServiceDep
from app.modules.users.schemas import UserRead
from app.modules.users.service import get_current_user

mapsRouter = APIRouter(prefix="/maps", tags=["Maps"])


@mapsRouter.get("", response_model=List[MapRead])
async def get_all_maps(
    service: MapServiceDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return await service.get_all_maps()


@mapsRouter.post("", response_model=MapRead)
async def create(
    map: MapCreate,
    service: MapServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.create_map(map, current_user)


@mapsRouter.patch("/{map_id}", response_model=MapRead)
async def patch_map(
    map_id: int,
    map: MapUpdate,
    service: MapServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.update_map(map_id, map, current_user)
