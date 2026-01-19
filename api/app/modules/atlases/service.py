from typing import Annotated, List

from fastapi import Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.modules.atlases.models import Atlas
from app.modules.atlases.repository import AtlasRepository
from app.modules.atlases.schemas import (
    AtlasBase,
    AtlasRead,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasUpdate,
)
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

        atlas_dict = atlas_update.model_dump(exclude_unset=True, exclude={"teams"})

        try:
            updated_atlas = await self.repository.update(atlas_id, atlas_dict)
        except ValueError as e:
            # Catch the ValueError from repo (invalid map id)
            raise HTTPException(status_code=404, detail=str(e))

        if not updated_atlas:
            raise HTTPException(status_code=404, detail="Atlas not found")

        return updated_atlas

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

        try:
            result = await self.repository.upsert_team_link(link.model_dump())
            return AtlasTeamLinkRead(**result.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    async def delete_atlas_team_link(
        self, atlas_id: int, team_id: int, current_user: UserRead
    ) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to remove a team from an atlas",
            )

        deleted = await self.repository.delete_team_link(atlas_id, team_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Link not found")
        return True

    async def get_all_atlases(self) -> List[Atlas]:
        return await self.repository.get_all()

    async def delete_atlas(self, atlas_id: int, current_user: UserRead) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise HTTPException(
                status_code=403, detail="You don't have permission to delete atlases"
            )

        deleted = await self.repository.delete(atlas_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Atlas not found")
        return True


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_atlas_service(session: SessionDep, settings: SettingsDep) -> AtlasService:
    repo = AtlasRepository(session, Atlas)
    return AtlasService(repo, settings)


AtlasServiceDep = Annotated[AtlasService, Depends(get_atlas_service)]
