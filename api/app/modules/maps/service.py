from typing import Annotated, List, Optional

from fastapi import Depends
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.atlases.models import Atlas
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
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise PermissionDeniedException(
                params={"detail": "map.create_permission_denied"}
            )

        existing_map = await self.repository.get_by_name(map.name)
        if existing_map:
            raise DuplicateEntityException(
                key="map.name_exists", params={"name": map.name}
            )

        # Verify Atlas exists
        atlas = await self.repository.session.exec(
            select(Atlas).where(Atlas.id == map.atlas_id)
        )
        if not atlas.first():
            raise EntityNotFoundException(entity="Atlas", params={"id": map.atlas_id})

        # Create Map (atlas_id is included in map.model_dump())
        new_map = await self.repository.create(map.model_dump())
        return await self.repository.get_by_name(new_map.name)

    async def update_map(
        self,
        map_id: int,
        map_update: MapUpdate,
        current_user: UserRead,
    ) -> MapRead:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise PermissionDeniedException(
                params={"detail": "map.update_permission_denied"}
            )

        map_db = await self.repository.get(map_id)
        if not map_db:
            raise EntityNotFoundException(entity="Map", params={"id": map_id})

        updated_map = await self.repository.update(
            map_id, map_update.model_dump(exclude_unset=True)
        )
        if not updated_map:
            raise EntityNotFoundException(entity="Map", params={"id": map_id})

        return updated_map

    async def get_map(self, map_id: int) -> Optional[Map]:
        map_obj = await self.repository.get(map_id)
        if not map_obj:
            raise EntityNotFoundException(entity="Map", params={"id": map_id})
        return map_obj

    async def delete_map(self, map_id: int, current_user: UserRead) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise PermissionDeniedException(
                params={"detail": "map.delete_permission_denied"}
            )

        deleted = await self.repository.delete(map_id)
        if not deleted:
            raise EntityNotFoundException(entity="Map", params={"id": map_id})
        return True

    async def get_all_maps(self) -> List[Map]:
        return await self.repository.get_all()


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_map_service(session: SessionDep, settings: SettingsDep) -> MapService:
    repo = MapRepository(session, Map)
    return MapService(repo, settings)


MapServiceDep = Annotated[MapService, Depends(get_map_service)]
