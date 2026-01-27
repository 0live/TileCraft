from typing import Annotated, List

from fastapi import Depends
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.enums.access_policy import AccessPolicy
from app.core.exceptions import (
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.atlases.repository import AtlasRepository
from app.modules.atlases.schemas import (
    AtlasBase,
    AtlasDetail,
    AtlasSummary,
    AtlasTeamLinkCreate,
    AtlasTeamLinkRead,
    AtlasTeamLinkUpdate,
    AtlasUpdate,
)
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail


class AtlasService:
    def __init__(self, repository: AtlasRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def create_atlas(
        self, atlas: AtlasBase, current_user: UserDetail
    ) -> AtlasDetail:
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

        return await self.repository.get(
            new_atlas.id,
            options=[selectinload(Atlas.teams), selectinload(Atlas.maps)],
        )

    async def get_atlas(self, atlas_id: int, current_user: UserDetail) -> AtlasDetail:
        atlas = await self.repository.get(
            atlas_id, options=[selectinload(Atlas.teams), selectinload(Atlas.maps)]
        )
        if not atlas:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )

        can_view = False
        if UserRole.ADMIN in current_user.roles:
            can_view = True
        elif atlas.created_by_id == current_user.id:
            can_view = True
        elif atlas.access_policy == AccessPolicy.PUBLIC:
            can_view = True
        else:
            user_team_ids = {t.id for t in current_user.teams}
            atlas_team_ids = {t.id for t in atlas.teams}
            if user_team_ids & atlas_team_ids:
                can_view = True

        if not can_view:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )

        return atlas

    async def get_all_atlases(self, current_user: UserDetail) -> List[AtlasSummary]:
        return await self.repository.get_all(
            filter_owner_id=current_user.id,
            filter_team_ids=[t.id for t in current_user.teams],
            admin_bypass=UserRole.ADMIN in current_user.roles,
        )

    async def update_atlas(
        self,
        atlas_id: int,
        atlas_update: AtlasUpdate,
        current_user: UserDetail,
    ) -> AtlasDetail:
        atlas = await self.repository.get(atlas_id)
        if not atlas:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )

        if not await self._has_manage_permission(atlas, current_user):
            raise PermissionDeniedException(
                params={"detail": "atlas.edit_permission_denied"}
            )

        atlas_dict = atlas_update.model_dump(exclude_unset=True, exclude={"teams"})
        atlas_dict = Atlas.add_audit_info(atlas_dict, current_user.id)

        await self.repository.update(atlas_id, atlas_dict)
        await self.repository.session.commit()

        return await self.repository.get(
            atlas_id, options=[selectinload(Atlas.teams), selectinload(Atlas.maps)]
        )

    async def delete_atlas(self, atlas_id: int, current_user: UserDetail) -> bool:
        atlas = await self.repository.get(atlas_id)
        if not atlas:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )

        if not await self._has_manage_permission(atlas, current_user):
            raise PermissionDeniedException(
                params={"detail": "atlas.delete_permission_denied"}
            )

        deleted = await self.repository.delete(atlas_id)
        if not deleted:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )
        await self.repository.session.commit()
        return True

    async def add_team_to_atlas(
        self,
        link: AtlasTeamLinkCreate,
        current_user: UserDetail,
    ) -> AtlasTeamLinkRead:
        atlas = await self.repository.get(link.atlas_id)
        if not atlas:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": link.atlas_id}
            )

        if not await self._has_manage_permission(atlas, current_user):
            raise PermissionDeniedException(
                params={"detail": "atlas.link_permission_denied"}
            )

        if await self.repository.get_team_link(link.atlas_id, link.team_id):
            raise DuplicateEntityException(
                key="atlas.team_already_linked",
                params={
                    "team_id": link.team_id,
                    "atlas_id": link.atlas_id,
                },
            )

        try:
            result = await self.repository.create_team_link(link.model_dump())
            await self.repository.session.commit()
            return AtlasTeamLinkRead(**result.model_dump())
        except ValueError as e:
            raise EntityNotFoundException(
                entity="Team",
                key="team.not_found",
                params={"detail": str(e)},
            )

    async def update_atlas_team_permissions(
        self,
        atlas_id: int,
        team_id: int,
        link_update: AtlasTeamLinkUpdate,
        current_user: UserDetail,
    ) -> AtlasTeamLinkRead:
        atlas = await self.repository.get(atlas_id)
        if not atlas:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )

        if not await self._has_manage_permission(atlas, current_user):
            raise PermissionDeniedException(
                params={"detail": "atlas.link_permission_denied"}
            )

        link = await self.repository.get_team_link(atlas_id, team_id)
        if not link:
            raise EntityNotFoundException(
                entity="TeamLink",
                key="atlas.team_not_linked",
                params={"team_id": team_id, "atlas_id": atlas_id},
            )

        update_data = link_update.model_dump(exclude_unset=True)
        result = await self.repository.update_team_link(link, update_data)
        await self.repository.session.commit()
        return AtlasTeamLinkRead(**result.model_dump())

    async def delete_atlas_team_link(
        self, atlas_id: int, team_id: int, current_user: UserDetail
    ) -> bool:
        atlas = await self.repository.get(atlas_id)
        if not atlas:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": atlas_id}
            )

        if not await self._has_manage_permission(atlas, current_user):
            raise PermissionDeniedException(
                params={"detail": "atlas.link_permission_denied"}
            )

        deleted = await self.repository.delete_team_link(atlas_id, team_id)
        if not deleted:
            raise DomainException(key="atlas.team_link_not_found")
        await self.repository.session.commit()
        return True

    async def _has_manage_permission(self, atlas: Atlas, user: UserDetail) -> bool:
        """Check if user is Admin, Creator, or has Team Manager rights."""
        if UserRole.ADMIN in user.roles:
            return True
        if atlas.created_by_id == user.id:
            return True
        return await self._check_team_manage_permission(atlas.id, user)

    async def _check_team_manage_permission(
        self, atlas_id: int, user: UserDetail
    ) -> bool:
        user_team_ids = [t.id for t in user.teams]
        if not user_team_ids:
            return False

        statement = select(AtlasTeamLink).where(
            AtlasTeamLink.atlas_id == atlas_id,
            AtlasTeamLink.team_id.in_(user_team_ids),
            AtlasTeamLink.can_manage_atlas,
        )
        result = await self.repository.session.exec(statement)
        return bool(result.first())


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_atlas_service(session: SessionDep, settings: SettingsDep) -> AtlasService:
    repo = AtlasRepository(session, Atlas)
    return AtlasService(repo, settings)


AtlasServiceDep = Annotated[AtlasService, Depends(get_atlas_service)]
