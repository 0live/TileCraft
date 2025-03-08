from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.services.maps import create_map, update_map
from app.db.maps import Map
from app.models.maps import MapRead, MapBase, MapUpdate
from app.models.atlases import AtlasRead
from app.models.users import UserRead
from app.services.users import get_current_user
from app.core.database import SessionDep


mapsRouter = APIRouter(prefix="/maps", tags=["Maps"])


@mapsRouter.get("", response_model=List[MapRead])
def get_all_atlases(
    session: SessionDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return session.exec(select(Map)).all()


@mapsRouter.post("", response_model=AtlasRead)
def register(
    map: MapBase,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return create_map(map, session, current_user)


@mapsRouter.patch("/{map_id}", response_model=MapRead)
def patch_user(
    map_id: int,
    map: MapUpdate,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return update_map(map_id, map, session, current_user)
