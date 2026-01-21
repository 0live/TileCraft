from typing import Annotated, List

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.exceptions import (
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
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
            raise PermissionDeniedException(
                params={"detail": "atlas.create_permission_denied"}
            )

        existing_atlas = await self.repository.get_by_name(atlas.name)
        if existing_atlas:
            raise DuplicateEntityException(
                key="atlas.name_exists", params={"name": atlas.name}
            )

        atlas_data = Atlas.add_audit_info(atlas.model_dump(), current_user.id)
        new_atlas = Atlas(**atlas_data)
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
            raise PermissionDeniedException()

        atlas_dict = atlas_update.model_dump(exclude_unset=True, exclude={"teams"})
        atlas_dict = Atlas.add_audit_info(atlas_dict, current_user.id)

        try:
            updated_atlas = await self.repository.update(atlas_id, atlas_dict)
        except ValueError as e:
            # Catch the ValueError from repo (invalid map id)
            # Assuming generic DomainException for now as it seems to be specific validation logic
            # Ideally this should be more specific, but for now we wrap it.
            raise DomainException(key="atlas.invalid_update", params={"detail": str(e)})

        if not updated_atlas:
            raise EntityNotFoundException(entity="Atlas", params={"id": atlas_id})

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
            raise PermissionDeniedException(
                params={"detail": "atlas.link_permission_denied"}
            )

        try:
            result = await self.repository.upsert_team_link(link.model_dump())
            return AtlasTeamLinkRead(**result.model_dump())
        except ValueError as e:
            raise EntityNotFoundException(entity="TeamLink", params={"detail": str(e)})

    async def delete_atlas_team_link(
        self, atlas_id: int, team_id: int, current_user: UserRead
    ) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise PermissionDeniedException(
                params={"detail": "atlas.link_permission_denied"}
            )

        deleted = await self.repository.delete_team_link(atlas_id, team_id)
        if not deleted:
            raise DomainException(key="atlas.team_link_not_found")
        return True

    async def get_all_atlases(self) -> List[Atlas]:
        return await self.repository.get_all()

    async def get_atlas(self, atlas_id: int) -> Atlas:
        atlas = await self.repository.get(atlas_id)
        if not atlas:
            raise EntityNotFoundException(entity="Atlas", params={"id": atlas_id})
        return atlas

    async def delete_atlas(self, atlas_id: int, current_user: UserRead) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise PermissionDeniedException(
                params={"detail": "atlas.delete_permission_denied"}
            )

        deleted = await self.repository.delete(atlas_id)
        if not deleted:
            raise EntityNotFoundException(entity="Atlas", params={"id": atlas_id})
        return True


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_atlas_service(session: SessionDep, settings: SettingsDep) -> AtlasService:
    repo = AtlasRepository(session, Atlas)
    return AtlasService(repo, settings)


AtlasServiceDep = Annotated[AtlasService, Depends(get_atlas_service)]
