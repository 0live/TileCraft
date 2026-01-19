from typing import Any, List, Optional

from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.maps.models import Map


class MapRepository(BaseRepository[Map]):
    """Repository for Map entities with eager loading of atlases relationship."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(Map.atlases)]

    async def get_by_name(self, name: str) -> Optional[Map]:
        """Get a map by name with atlases loaded."""
        from sqlmodel import select

        query = select(self.model).where(self.model.name == name)
        for option in self.get_load_options():
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_with_atlases(self, id: int) -> Optional[Map]:
        """Alias for get() - kept for backwards compatibility."""
        return await self.get(id)
