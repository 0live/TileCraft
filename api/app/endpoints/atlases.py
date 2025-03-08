from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.services.atlases import create_atlas
from app.models.atlases import AtlasBase, AtlasRead, AtlasUpdate
from app.db.atlases import Atlas
from app.models.users import UserRead
from app.services.users import get_current_user
from app.core.database import SessionDep


atlasesRouter = APIRouter(prefix="/atlases", tags=["Atlases"])


@atlasesRouter.get("", response_model=List[AtlasRead])
def get_all_atlases(
    session: SessionDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return session.exec(select(Atlas)).all()


@atlasesRouter.post("", response_model=AtlasRead)
def register(
    atlas: AtlasBase,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return create_atlas(atlas, session, current_user)


@atlasesRouter.patch("/{atlas_id}", response_model=AtlasRead)
def patch_user(
    atlas_id: int,
    atlas: AtlasUpdate,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return update_atlas(atlas_id, atlas, session, current_user)
