from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.modules.atlases.schemas import (
    AtlasBase,
    AtlasRead,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasUpdate,
)
from app.modules.atlases.service import AtlasServiceDep
from app.modules.users.schemas import UserRead
from app.modules.users.service import get_current_user

atlasesRouter = APIRouter(prefix="/atlases", tags=["Atlases"])


@atlasesRouter.get("", response_model=List[AtlasRead])
async def get_all_atlases(
    service: AtlasServiceDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return await service.get_all_atlases()


@atlasesRouter.get("/{atlas_id}", response_model=AtlasRead)
async def get_atlas(
    atlas_id: int,
    service: AtlasServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return await service.get_atlas(atlas_id)


@atlasesRouter.post("", response_model=AtlasRead)
async def create(
    atlas: AtlasBase,
    service: AtlasServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.create_atlas(atlas, current_user)


@atlasesRouter.patch("/{atlas_id}", response_model=AtlasRead)
async def patch_atlas(
    atlas_id: int,
    atlas: AtlasUpdate,
    service: AtlasServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.update_atlas(atlas_id, atlas, current_user)


@atlasesRouter.post("/team", response_model=AtlasTeamLinkRead)
async def create_link(
    link: AtlasTeamLinkCreate,
    service: AtlasServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.manage_atlas_team_link(link, current_user)


@atlasesRouter.delete("/{atlas_id}")
async def delete(
    atlas_id: int,
    service: AtlasServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.delete_atlas(atlas_id, current_user)


@atlasesRouter.delete("/{atlas_id}/team/{team_id}")
async def delete_link(
    atlas_id: int,
    team_id: int,
    service: AtlasServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.delete_atlas_team_link(atlas_id, team_id, current_user)
