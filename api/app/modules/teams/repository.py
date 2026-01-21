from typing import Any, List

from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.teams.models import Team


class TeamRepository(BaseRepository[Team]):
    """Repository for Team entities with eager loading of users relationship."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(Team.users)]
