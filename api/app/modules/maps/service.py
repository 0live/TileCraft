from typing import Annotated, List, Optional

from fastapi import Depends, HTTPException
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
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
            raise HTTPException(
                status_code=403, detail="You don't have permission to create maps"
            )

        existing_map = await self.repository.get_by_name(map.name)
        if existing_map:
            raise HTTPException(status_code=400, detail="This name already exists")

        # Verify Atlas exists
        atlas = await self.repository.session.exec(
            select(Atlas).where(Atlas.id == map.atlas_id)
        )
        if not atlas.first():
            raise HTTPException(status_code=404, detail="Atlas not found")

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
            raise HTTPException(status_code=403, detail="Forbidden")

        map_db = await self.repository.get(map_id)
        if not map_db:
            raise HTTPException(status_code=404, detail="Map not found")

        # We exclude unset fields.
        # Note: MapUpdate schema no longer has 'atlas_id' (immutable).
        updated_map = await self.repository.update(
            map_id, map_update.model_dump(exclude_unset=True)
        )
        if not updated_map:
            raise HTTPException(status_code=404, detail="Map not found")

        return updated_map

    async def get_map(self, map_id: int) -> Optional[Map]:
        map_obj = await self.repository.get(map_id)
        if not map_obj:
            raise HTTPException(status_code=404, detail="Map not found")
        return map_obj

    async def delete_map(self, map_id: int, current_user: UserRead) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_ATLASES_AND_MAPS]
        ):
            raise HTTPException(
                status_code=403, detail="You don't have permission to delete maps"
            )

        deleted = await self.repository.delete(map_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Map not found")
        return True

    async def get_all_maps(self) -> List[Map]:
        return await self.repository.get_all()


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_map_service(session: SessionDep, settings: SettingsDep) -> MapService:
    repo = MapRepository(session, Map)
    return MapService(repo, settings)


MapServiceDep = Annotated[MapService, Depends(get_map_service)]
