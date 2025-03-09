from typing import Optional
from fastapi import HTTPException
from sqlmodel import select
from app.models.maps import MapBase, MapRead, MapUpdate
from app.db.maps import Map
from app.db.atlases import Atlas
from app.models.user_roles import UserRole
from app.models.users import UserRead
from app.core.database import SessionDep


def create_map(map: MapBase, session: SessionDep, current_user: UserRead) -> MapRead:
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
    ):
        raise HTTPException(
            status_code=403, detail="You don't have permission to create maps"
        )
    if session.exec(select(Map).where(Map.name == map.name)).first():
        raise HTTPException(status_code=400, detail="This name already exists")
    new_map = Map(**map.model_dump(exclude={"atlases"}))
    if map.atlases is not None:
        for atlas_id in map.atlases:
            atlas = session.exec(select(Atlas).where(Atlas.id == atlas_id)).first()
            if atlas:
                new_map.atlases.append(atlas)
            else:
                raise HTTPException(status_code=404, detail="Atlas not found")
    session.add(new_map)
    session.commit()
    session.refresh(new_map)
    return MapRead(**new_map.model_dump())


def update_map(
    map_id: int,
    map: MapUpdate,
    session: SessionDep,
    current_user: UserRead,
) -> Optional[MapRead]:
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    map_db = session.exec(select(Map).where(Map.id == map_id)).first()
    if map_db is None:
        raise HTTPException(status_code=404, detail="Map not found")

    map_dict = map.model_dump(exclude_unset=True, exclude={"atlases"})

    if map.atlases is not None:
        for atlas_id in map.atlases:
            if atlas_id in map_db.atlases:
                map_db.atlases.remove(atlas_id)
            else:
                atlas = session.exec(select(Atlas).where(Atlas.id == atlas_id)).first()
                if atlas:
                    map_db.atlases.append(atlas)
                else:
                    raise HTTPException(status_code=404, detail="Atlas not found")

    for key, value in map_dict.items():
        setattr(map_db, key, value)
    session.add(map_db)
    session.commit()
    session.refresh(map_db)
    return MapRead.model_validate(map_db)
