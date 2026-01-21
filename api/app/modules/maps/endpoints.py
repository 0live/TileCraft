from typing import List

from fastapi import APIRouter, Depends

from app.core.auth_dependencies import get_current_user
from app.modules.maps.schemas import MapCreate, MapRead, MapUpdate
from app.modules.maps.service import MapServiceDep
from app.modules.users.schemas import UserRead

mapsRouter = APIRouter(prefix="/maps", tags=["Maps"])


@mapsRouter.get("", response_model=List[MapRead])
async def get_all_maps(
    service: MapServiceDep, current_user: UserRead = Depends(get_current_user)
):
    return await service.get_all_maps()


@mapsRouter.get("/{map_id}", response_model=MapRead)
async def get_map(
    map_id: int,
    service: MapServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.get_map(map_id)


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


@mapsRouter.delete("/{map_id}")
async def delete_map(
    map_id: int,
    service: MapServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.delete_map(map_id, current_user)
