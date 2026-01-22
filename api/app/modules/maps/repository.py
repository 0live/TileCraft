from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.maps.models import Map


class MapRepository(BaseRepository[Map]):
    """Repository for Map entities."""

    async def get_by_atlas_and_name(self, atlas_id: int, name: str) -> Map | None:
        """Get a map by atlas_id and name."""
        query = select(Map).where(Map.atlas_id == atlas_id, Map.name == name)
        result = await self.session.exec(query)
        return result.first()
