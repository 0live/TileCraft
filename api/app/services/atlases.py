from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.database import SessionDep
from app.db.atlases import Atlas, AtlasTeamLink
from app.db.maps import Map
from app.db.teams import Team
from app.models.atlases import (
    AtlasBase,
    AtlasRead,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasUpdate,
)
from app.models.user_roles import UserRole
from app.models.users import UserRead


async def create_atlas(
    atlas: AtlasBase, session: SessionDep, current_user: UserRead
) -> AtlasRead:
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
    ):
        raise HTTPException(
            status_code=403, detail="You don't have permission to create atlases"
        )
    existing_atlas_result = await session.exec(
        select(Atlas).where(Atlas.name == atlas.name)
    )
    if existing_atlas_result.first():
        raise HTTPException(status_code=400, detail="This name already exists")
    new_atlas = Atlas(**atlas.model_dump())
    session.add(new_atlas)
    await session.commit()
    await session.refresh(new_atlas)

    # Reload with relationships for Pydantic validation
    result = await session.exec(
        select(Atlas)
        .where(Atlas.id == new_atlas.id)
        .options(selectinload(Atlas.teams), selectinload(Atlas.maps))
    )
    new_atlas_loaded = result.first()
    return AtlasRead(**new_atlas_loaded.model_dump())


async def update_atlas(
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
    atlas_db_result = await session.exec(select(Atlas).where(Atlas.id == atlas_id))
    atlas_db = atlas_db_result.first()
    if atlas_db is None:
        raise HTTPException(status_code=404, detail="Atlas not found")

    atlas_dict = atlas.model_dump(exclude_unset=True, exclude={"teams", "maps"})

    if atlas.maps is not None:
        for map_id in atlas.maps:
            if map_id in atlas_db.maps:
                atlas_db.maps.remove(map_id)
            else:
                map_result = await session.exec(select(Map).where(Map.id == map_id))
                map = map_result.first()
                if map:
                    atlas_db.maps.append(map)
                else:
                    raise HTTPException(status_code=404, detail="Map not found")

    for key, value in atlas_dict.items():
        setattr(atlas_db, key, value)
    session.add(atlas_db)
    await session.commit()
    await session.refresh(atlas_db)

    # Reload with relationships for Pydantic validation
    result = await session.exec(
        select(Atlas)
        .where(Atlas.id == atlas_db.id)
        .options(selectinload(Atlas.teams), selectinload(Atlas.maps))
    )
    atlas_db_loaded = result.first()
    return AtlasRead.model_validate(atlas_db_loaded)


async def manage_atlas_team_link(
    link: AtlasTeamLinkCreate,
    session: SessionDep,
    current_user: UserRead,
):
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
    ):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to add a team to an atlas",
        )
    team_result = await session.exec(select(Team).where(Team.id == link.team_id))
    team = team_result.first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    existing_link_result = await session.exec(
        select(AtlasTeamLink).where(
            AtlasTeamLink.atlas_id == link.atlas_id
            and AtlasTeamLink.team_id == link.team_id
        )
    )
    existing_link = existing_link_result.first()
    if existing_link:
        existing_link.can_manage_atlas = bool(link.can_manage_atlas)
        existing_link.can_create_maps = bool(link.can_create_maps)
        existing_link.can_edit_maps = bool(link.can_edit_maps)
        session.add(existing_link)
        await session.commit()
        await session.refresh(existing_link)
        return AtlasTeamLinkRead(**existing_link.model_dump())
    else:
        new_link = AtlasTeamLink(**link.model_dump())
        session.add(new_link)
        await session.commit()
        await session.refresh(new_link)
        return AtlasTeamLinkRead(**new_link.model_dump())
