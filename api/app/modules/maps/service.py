from typing import Annotated, List

from fastapi import Depends
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.enums.access_policy import AccessPolicy
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.maps.models import Map
from app.modules.maps.repository import MapRepository
from app.modules.maps.schemas import MapCreate, MapRead, MapUpdate
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserRead


class MapService:
    def __init__(self, repository: MapRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def create_map(self, map: MapCreate, current_user: UserRead) -> MapRead:
        query = select(Atlas).where(Atlas.id == map.atlas_id)
        atlas_obj = (await self.repository.session.exec(query)).first()
        if not atlas_obj:
            raise EntityNotFoundException(
                entity="Atlas", key="atlas.not_found", params={"id": map.atlas_id}
            )

        can_create = (
            any(
                role in current_user.roles
                for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
            )
            or atlas_obj.created_by_id == current_user.id
            or await self._check_team_map_permission(
                map.atlas_id, current_user, "create"
            )
        )

        if not can_create:
            raise PermissionDeniedException(
                params={"detail": "map.create_permission_denied"}
            )

        existing_map = await self.repository.get_by_atlas_and_name(
            map.atlas_id, map.name
        )
        if existing_map:
            raise DuplicateEntityException(
                key="map.name_exists", params={"name": map.name}
            )

        map_data = Map.add_audit_info(map.model_dump(), current_user.id)
        new_map = await self.repository.create(map_data)
        return await self.repository.get_by_name(new_map.name)

    async def get_map(self, map_id: int, current_user: UserRead) -> Map:
        map_obj = await self.repository.get(map_id)
        if not map_obj:
            raise EntityNotFoundException(
                entity="Map", key="map.not_found", params={"id": map_id}
            )

        can_view = (
            any(
                role in current_user.roles
                for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
            )
            or map_obj.access_policy == AccessPolicy.PUBLIC
            or map_obj.created_by_id == current_user.id
            or await self._check_team_map_permission(
                map_obj.atlas_id, current_user, "read"
            )
        )

        if not can_view:
            raise EntityNotFoundException(
                entity="Map", key="map.not_found", params={"id": map_id}
            )

        return map_obj

    async def get_all_maps(self, current_user: UserRead) -> List[Map]:
        admin_bypass = UserRole.ADMIN in current_user.roles

        return await self.repository.get_all(
            filter_owner_id=current_user.id,
            filter_team_ids=[t.id for t in current_user.teams],
            admin_bypass=admin_bypass,
        )

    async def update_map(
        self,
        map_id: int,
        map_update: MapUpdate,
        current_user: UserRead,
    ) -> MapRead:
        map_db = await self.repository.get(map_id)
        if not map_db:
            raise EntityNotFoundException(
                entity="Map", key="map.not_found", params={"id": map_id}
            )

        can_edit = (
            UserRole.ADMIN in current_user.roles
            or map_db.created_by_id == current_user.id
            or await self._check_team_map_permission(
                map_db.atlas_id, current_user, "edit"
            )
        )

        if not can_edit:
            raise PermissionDeniedException(
                params={"detail": "map.update_permission_denied"}
            )

        update_data = map_update.model_dump(exclude_unset=True)

        new_name = update_data.get("name", map_db.name)
        new_atlas_id = update_data.get("atlas_id", map_db.atlas_id)
        if new_name != map_db.name or new_atlas_id != map_db.atlas_id:
            existing_map = await self.repository.get_by_atlas_and_name(
                new_atlas_id, new_name
            )
            if existing_map:
                raise DuplicateEntityException(
                    key="map.name_exists", params={"name": new_name}
                )

        update_data = Map.add_audit_info(update_data, current_user.id)
        updated_map = await self.repository.update(map_id, update_data)
        return updated_map

    async def delete_map(self, map_id: int, current_user: UserRead) -> bool:
        map_obj = await self.repository.get(map_id)
        if not map_obj:
            raise EntityNotFoundException(
                entity="Map", key="map.not_found", params={"id": map_id}
            )

        can_delete = (
            UserRole.ADMIN in current_user.roles
            or map_obj.created_by_id == current_user.id
            or await self._check_team_map_permission(
                map_obj.atlas_id, current_user, "edit"
            )
        )

        if not can_delete:
            raise PermissionDeniedException(
                params={"detail": "map.delete_permission_denied"}
            )

        deleted = await self.repository.delete(map_id)
        if not deleted:
            raise EntityNotFoundException(
                entity="Map", key="map.not_found", params={"id": map_id}
            )
        return True

    async def _check_team_map_permission(
        self, atlas_id: int, user: UserRead, permission_type: str = "read"
    ) -> bool:
        user_team_ids = [t.id for t in user.teams]
        if not user_team_ids:
            return False

        query = select(AtlasTeamLink).where(
            AtlasTeamLink.atlas_id == atlas_id,
            AtlasTeamLink.team_id.in_(user_team_ids),
        )

        if permission_type == "create":
            query = query.where(AtlasTeamLink.can_create_maps)
        elif permission_type == "edit":
            query = query.where(AtlasTeamLink.can_edit_maps)
        elif permission_type == "read":
            query = query.where(AtlasTeamLink.team_id.in_(user_team_ids))

        result = await self.repository.session.exec(query)
        return bool(result.first())


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_map_service(session: SessionDep, settings: SettingsDep) -> MapService:
    repo = MapRepository(session, Map)
    return MapService(repo, settings)


MapServiceDep = Annotated[MapService, Depends(get_map_service)]
