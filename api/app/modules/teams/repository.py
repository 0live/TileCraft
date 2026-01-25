from typing import Any, List, Optional

from sqlmodel import select

from app.core.enums.access_policy import AccessPolicy
from app.core.repository import BaseRepository
from app.modules.teams.models import Team, UserTeamLink
from app.modules.users.models import User


class TeamRepository(BaseRepository[Team]):
    """Repository for Team entities."""

    async def get_all(
        self,
        user: Optional[User] = None,
        options: Optional[List[Any]] = None,
        filter_by_access: bool = True,
    ) -> List[Team]:
        query = select(Team).distinct()
        if options:
            for option in options:
                query = query.options(option)

        if filter_by_access and user:
            query = query.outerjoin(UserTeamLink)
            query = query.where(
                (Team.created_by_id == user.id)
                | (Team.access_policy == AccessPolicy.PUBLIC)
                | (UserTeamLink.user_id == user.id)
            )

        result = await self.session.exec(query)
        return list(result.all())
