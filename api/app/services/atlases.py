from typing import Optional
from fastapi import HTTPException
from sqlmodel import select
from app.db.maps import Map
from app.db.atlases import Atlas
from app.models.atlases import AtlasBase, AtlasRead, AtlasUpdate
from app.models.user_roles import UserRole
from app.models.users import UserRead
from app.db.teams import Team
from app.core.database import SessionDep


def create_atlas(
    atlas: AtlasBase, session: SessionDep, current_user: UserRead
) -> AtlasRead:
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
    ):
        raise HTTPException(
            status_code=403, detail="You don't have permission to create atlases"
        )
    if session.exec(select(Atlas).where(Atlas.name == atlas.name)).first():
        raise HTTPException(status_code=400, detail="This name already exists")
    new_atlas = Atlas(**atlas.model_dump())
    session.add(new_atlas)
    session.commit()
    session.refresh(new_atlas)
    return AtlasRead(**new_atlas.model_dump())


def update_atlas(
    atlas_id: int,
    atlas: AtlasUpdate,
    session: SessionDep,
    current_user: UserRead,
) -> Optional[AtlasRead]:
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    atlas_db = session.exec(select(Atlas).where(Atlas.id == atlas_id)).first()
    if atlas_db is None:
        raise HTTPException(status_code=404, detail="Atlas not found")

    atlas_dict = atlas.model_dump(exclude_unset=True, exclude={"teams", "maps"})

    if atlas.teams is not None:
        for team_id in atlas.teams:
            if team_id in atlas_db.teams:
                atlas_db.teams.remove(team_id)
            else:
                team = session.exec(select(Team).where(Team.id == team_id)).first()
                if team:
                    atlas_db.teams.append(team)
                else:
                    raise HTTPException(status_code=404, detail="Team not found")

    if atlas.maps is not None:
        for map_id in atlas.maps:
            if map_id in atlas_db.maps:
                atlas_db.maps.remove(map_id)
            else:
                map = session.exec(select(Map).where(Map.id == map_id)).first()
                if map:
                    atlas_db.maps.append(map)
                else:
                    raise HTTPException(status_code=404, detail="Map not found")

    for key, value in atlas_dict.items():
        setattr(atlas_db, key, value)
    session.add(atlas_db)
    session.commit()
    session.refresh(atlas_db)
    return AtlasRead.model_validate(atlas_db)
