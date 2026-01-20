from typing import Any, List

from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.teams.models import Team


class TeamRepository(BaseRepository[Team]):
    """Repository for Team entities with eager loading of users relationship."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(Team.users)]

    async def get_by_name(self, name: str):
        """Get a team by name with users loaded."""
        from sqlmodel import select

        query = select(self.model).where(self.model.name == name)
        for option in self.get_load_options():
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()
