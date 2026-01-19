from typing import Annotated, List

from fastapi import Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.modules.teams.models import Team
from app.modules.teams.repository import TeamRepository
from app.modules.teams.schemas import TeamBase, TeamRead
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserRead


class TeamService:
    def __init__(self, repository: TeamRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def create_team(self, team: TeamBase, current_user: UserRead) -> TeamRead:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise HTTPException(
                status_code=403, detail="You don't have permission to create teams"
            )

        existing_team = await self.repository.get_by_name(team.name)
        if existing_team:
            raise HTTPException(status_code=400, detail="This name already exists")

        new_team = await self.repository.create(team.model_dump())

        # Reload or return carefully.
        # Since it's new, users list is empty.
        # But for TeamRead to validate without erroring on missing attribute 'users':
        # we should ensure it's loaded as empty list.
        # BaseRepository refreshes, but without relationships.
        # Accessing new_team.users might trigger lazy load failure.

        # We can manually set it if we know it works, or reload.
        return await self.repository.get_by_name(new_team.name)

    async def get_all_teams(self) -> List[Team]:
        return await self.repository.get_all()


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_team_service(session: SessionDep, settings: SettingsDep) -> TeamService:
    repo = TeamRepository(session, Team)
    return TeamService(repo, settings)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
