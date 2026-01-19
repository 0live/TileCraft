from typing import Annotated, List

from fastapi import Depends, HTTPException
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.atlases.repository import AtlasRepository
from app.modules.atlases.schemas import (
    AtlasBase,
    AtlasRead,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasUpdate,
)
from app.modules.maps.models import Map
from app.modules.teams.models import Team
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserRead


class AtlasService:
    def __init__(self, repository: AtlasRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def create_atlas(self, atlas: AtlasBase, current_user: UserRead) -> AtlasRead:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise HTTPException(
                status_code=403, detail="You don't have permission to create atlases"
            )

        existing_atlas = await self.repository.get_by_name(atlas.name)
        if existing_atlas:
            raise HTTPException(status_code=400, detail="This name already exists")

        new_atlas = Atlas(**atlas.model_dump())
        self.repository.session.add(new_atlas)
        await self.repository.session.commit()
        await self.repository.session.refresh(new_atlas)

        # Reload with relationships
        return await self.repository.get_by_name(new_atlas.name)

    async def update_atlas(
        self,
        atlas_id: int,
        atlas_update: AtlasUpdate,
        current_user: UserRead,
    ) -> AtlasRead:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise HTTPException(status_code=403, detail="Forbidden")

        atlas_db = await self.repository.get_with_relations(atlas_id)
        if not atlas_db:
            raise HTTPException(status_code=404, detail="Atlas not found")

        atlas_dict = atlas_update.model_dump(
            exclude_unset=True, exclude={"teams", "maps"}
        )

        if atlas_update.maps is not None:
            current_map_ids = {m.id for m in atlas_db.maps}
            for map_id in atlas_update.maps:
                if map_id in current_map_ids:
                    # Remove
                    map_to_remove = next(m for m in atlas_db.maps if m.id == map_id)
                    atlas_db.maps.remove(map_to_remove)
                else:
                    # Add
                    map_result = await self.repository.session.exec(
                        select(Map).where(Map.id == map_id)
                    )
                    map_obj = map_result.first()
                    if map_obj:
                        atlas_db.maps.append(map_obj)
                    else:
                        raise HTTPException(status_code=404, detail="Map not found")

        for key, value in atlas_dict.items():
            setattr(atlas_db, key, value)

        self.repository.session.add(atlas_db)
        await self.repository.session.commit()
        await self.repository.session.refresh(atlas_db)

        return await self.repository.get_with_relations(atlas_db.id)

    async def manage_atlas_team_link(
        self,
        link: AtlasTeamLinkCreate,
        current_user: UserRead,
    ) -> AtlasTeamLinkRead:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to add a team to an atlas",
            )

        team_result = await self.repository.session.exec(
            select(Team).where(Team.id == link.team_id)
        )
        team = team_result.first()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")

        existing_link_result = await self.repository.session.exec(
            select(AtlasTeamLink).where(
                AtlasTeamLink.atlas_id == link.atlas_id,
                AtlasTeamLink.team_id == link.team_id,
            )
        )
        existing_link = existing_link_result.first()
        if existing_link:
            existing_link.can_manage_atlas = bool(link.can_manage_atlas)
            existing_link.can_create_maps = bool(link.can_create_maps)
            existing_link.can_edit_maps = bool(link.can_edit_maps)
            self.repository.session.add(existing_link)
            await self.repository.session.commit()
            await self.repository.session.refresh(existing_link)
            return AtlasTeamLinkRead(**existing_link.model_dump())
        else:
            new_link = AtlasTeamLink(**link.model_dump())
            self.repository.session.add(new_link)
            await self.repository.session.commit()
            await self.repository.session.refresh(new_link)
            return AtlasTeamLinkRead(**new_link.model_dump())

    async def get_all_atlases(self) -> List[Atlas]:
        return await self.repository.get_all()


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_atlas_service(session: SessionDep, settings: SettingsDep) -> AtlasService:
    repo = AtlasRepository(session, Atlas)
    return AtlasService(repo, settings)


AtlasServiceDep = Annotated[AtlasService, Depends(get_atlas_service)]
