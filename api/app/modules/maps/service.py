from typing import Annotated, List

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

        # We need to handle atlases relationship manually before creation or after?
        # MapBase has atlases: Optional[List[int]]
        # BaseRepository.create takes dict and creates model.
        # But if we pass list of IDs to relationship field, SQLModel might not handle it directly unless we process it.
        # The existing logic did: new_map = Map(...exclude atlases); then manually appended atlases.

        map_dict = map.model_dump(exclude={"atlases"})
        new_map = Map(**map_dict)

        if map.atlases is not None:
            for atlas_id in map.atlases:
                atlas = await self.repository.session.exec(
                    select(Atlas).where(Atlas.id == atlas_id)
                )
                atlas_obj = atlas.first()
                if atlas_obj:
                    new_map.atlases.append(atlas_obj)
                else:
                    raise HTTPException(status_code=404, detail="Atlas not found")

        self.repository.session.add(new_map)
        await self.repository.session.commit()
        await self.repository.session.refresh(new_map)

        # Reload to ensure atlases are loaded
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

        map_db = await self.repository.get_with_atlases(map_id)
        if not map_db:
            raise HTTPException(status_code=404, detail="Map not found")

        map_dict = map_update.model_dump(exclude_unset=True, exclude={"atlases"})

        if map_update.atlases is not None:
            # We need to handle list diff
            current_atlas_ids = {a.id for a in map_db.atlases}

            # Logic from original service:
            # if atlas_id in map_db.atlases (list of IDs? No, list of Atlas in new model?)
            # Original code: if atlas_id in map_db.atlases: remove else add.
            # But map_db.atlases is List[Atlas]. So `atlas_id in map_db.atlases` fails for int.
            # I fixed this in User service. Same here.

            for atlas_id in map_update.atlases:
                if atlas_id in current_atlas_ids:
                    # Remove
                    atlas_to_remove = next(
                        a for a in map_db.atlases if a.id == atlas_id
                    )
                    map_db.atlases.remove(atlas_to_remove)
                else:
                    # Add
                    atlas = await self.repository.session.exec(
                        select(Atlas).where(Atlas.id == atlas_id)
                    )
                    atlas_obj = atlas.first()
                    if atlas_obj:
                        map_db.atlases.append(atlas_obj)
                    else:
                        raise HTTPException(status_code=404, detail="Atlas not found")

        for key, value in map_dict.items():
            setattr(map_db, key, value)

        self.repository.session.add(map_db)
        await self.repository.session.commit()
        await self.repository.session.refresh(map_db)

        return await self.repository.get_with_atlases(map_db.id)

    async def get_all_maps(self) -> List[Map]:
        return await self.repository.get_all()


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_map_service(session: SessionDep, settings: SettingsDep) -> MapService:
    repo = MapRepository(session, Map)
    return MapService(repo, settings)


MapServiceDep = Annotated[MapService, Depends(get_map_service)]
