from typing import Any, List, Optional

from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.teams.models import Team
from app.modules.users.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User entities with eager loading of teams relationship."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(User.teams).selectinload(Team.users)]

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username with teams loaded."""
        from sqlmodel import select

        query = select(self.model).where(self.model.username == username)
        for option in self.get_load_options():
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_with_teams(self, id: int) -> Optional[User]:
        """Alias for get() - kept for backwards compatibility."""
        return await self.get(id)
