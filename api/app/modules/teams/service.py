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

        # The repository now handles reloading with relationships automatically
        return await self.repository.create(team.model_dump())

    async def get_team_by_id(self, id: int) -> Team:
        team = await self.repository.get(id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team

    async def update_team(
        self, id: int, team_update: TeamBase, current_user: UserRead
    ) -> Team:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise HTTPException(
                status_code=403, detail="You don't have permission to update teams"
            )
        team = await self.get_team_by_id(id)

        if team_update.name != team.name:
            existing_team = await self.repository.get_by_name(team_update.name)
            if existing_team:
                raise HTTPException(status_code=400, detail="This name already exists")

        return await self.repository.update(
            id, team_update.model_dump(exclude_unset=True)
        )

    async def get_all_teams(self) -> List[Team]:
        return await self.repository.get_all()

    async def delete_team(self, id: int) -> bool:
        return await self.repository.delete(id)


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_team_service(session: SessionDep, settings: SettingsDep) -> TeamService:
    repo = TeamRepository(session, Team)
    return TeamService(repo, settings)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
