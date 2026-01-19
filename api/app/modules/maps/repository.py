from typing import Optional

from app.core.repository import BaseRepository
from app.modules.maps.models import Map


class MapRepository(BaseRepository[Map]):
    """Repository for Map entities."""

    async def get_by_name(self, name: str) -> Optional[Map]:
        """Get a map by name."""
        from sqlmodel import select

        query = select(self.model).where(self.model.name == name)
        # Use default get_load_options from BaseRepository (empty list)
        for option in self.get_load_options():
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()
