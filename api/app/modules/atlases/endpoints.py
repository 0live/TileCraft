from typing import List

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.modules.atlases.schemas import (
    AtlasBase,
    AtlasDetail,
    AtlasSummary,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasTeamLinkUpdate,
    AtlasUpdate,
)
from app.modules.atlases.service import AtlasServiceDep
from app.modules.users.schemas import UserDetail

atlasesRouter = APIRouter(prefix="/atlases", tags=["Atlases"])


@atlasesRouter.get("", response_model=List[AtlasSummary])
async def get_all_atlases(
    service: AtlasServiceDep, current_user: UserDetail = Depends(get_current_user)
):
    return await service.get_all_atlases(current_user)


@atlasesRouter.get("/{atlas_id}", response_model=AtlasDetail)
async def get_atlas(
    atlas_id: int,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.get_atlas(atlas_id, current_user)


@atlasesRouter.post("", response_model=AtlasDetail)
async def create(
    atlas: AtlasBase,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.create_atlas(atlas, current_user)


@atlasesRouter.patch("/{atlas_id}", response_model=AtlasDetail)
async def patch_atlas(
    atlas_id: int,
    atlas: AtlasUpdate,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.update_atlas(atlas_id, atlas, current_user)


@atlasesRouter.post("/team", response_model=AtlasTeamLinkRead)
async def create_link(
    link: AtlasTeamLinkCreate,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.add_team_to_atlas(link, current_user)


@atlasesRouter.patch("/{atlas_id}/team/{team_id}", response_model=AtlasTeamLinkRead)
async def update_link(
    atlas_id: int,
    team_id: int,
    link: AtlasTeamLinkUpdate,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.update_atlas_team_permissions(
        atlas_id, team_id, link, current_user
    )


@atlasesRouter.delete("/{atlas_id}")
async def delete(
    atlas_id: int,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.delete_atlas(atlas_id, current_user)


@atlasesRouter.delete("/{atlas_id}/team/{team_id}")
async def delete_link(
    atlas_id: int,
    team_id: int,
    service: AtlasServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.delete_atlas_team_link(atlas_id, team_id, current_user)
