from typing import Any, List, Optional

from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.atlases.models import Atlas


class AtlasRepository(BaseRepository[Atlas]):
    """Repository for Atlas entities with eager loading of teams and maps relationships."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(Atlas.teams), selectinload(Atlas.maps)]

    async def get_by_name(self, name: str) -> Optional[Atlas]:
        """Get an atlas by name with relations loaded."""
        from sqlmodel import select

        query = select(self.model).where(self.model.name == name)
        for option in self.get_load_options():
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_with_relations(self, id: int) -> Optional[Atlas]:
        """Alias for get() - kept for backwards compatibility."""
        return await self.get(id)
