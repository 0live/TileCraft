from typing import Any, List, Optional

from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.users.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    async def get_by_username(
        self, username: str, options: Optional[List[Any]] = None
    ) -> Optional[User]:
        query = select(self.model).where(self.model.username == username)
        if options:
            for option in options:
                query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_by_email(
        self, email: str, options: Optional[List[Any]] = None
    ) -> Optional[User]:
        query = select(self.model).where(self.model.email == email)
        if options:
            for option in options:
                query = query.options(option)
        result = await self.session.exec(query)
        return result.first()
