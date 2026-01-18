from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.database import SessionDep
from app.db.atlases import Atlas
from app.models.atlases import (
    AtlasBase,
    AtlasRead,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasUpdate,
)
from app.models.users import UserRead
from app.services.atlases import create_atlas, manage_atlas_team_link, update_atlas
from app.services.users import get_current_user

atlasesRouter = APIRouter(prefix="/atlases", tags=["Atlases"])


@atlasesRouter.get("", response_model=List[AtlasRead])
async def get_all_atlases(
    session: SessionDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    result = await session.exec(
        select(Atlas).options(selectinload(Atlas.teams), selectinload(Atlas.maps))
    )
    return result.all()


@atlasesRouter.post("", response_model=AtlasRead)
async def create(
    atlas: AtlasBase,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await create_atlas(atlas, session, current_user)


@atlasesRouter.patch("/{atlas_id}", response_model=AtlasRead)
async def patch_atlas(
    atlas_id: int,
    atlas: AtlasUpdate,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await update_atlas(atlas_id, atlas, session, current_user)


# Add endpoint for creating AtlasTeamLink
@atlasesRouter.post("/team", response_model=AtlasTeamLinkRead)
async def create_link(
    link: AtlasTeamLinkCreate,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await manage_atlas_team_link(link, session, current_user)
