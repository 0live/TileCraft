from typing import Annotated, List

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
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
            raise PermissionDeniedException(
                params={"detail": "team.create_permission_denied"}
            )

        existing_team = await self.repository.get_by_name(team.name)
        if existing_team:
            raise DuplicateEntityException(
                key="team.name_exists", params={"name": team.name}
            )

        team_data = Team.add_audit_info(team.model_dump(), current_user.id)
        return await self.repository.create(team_data)

    async def get_team_by_id(self, id: int) -> Team:
        team = await self.repository.get(id)
        if not team:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": id}
            )
        return team

    async def update_team(
        self, id: int, team_update: TeamBase, current_user: UserRead
    ) -> Team:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise PermissionDeniedException(
                params={"detail": "team.update_permission_denied"}
            )
        team = await self.get_team_by_id(id)

        if team_update.name != team.name:
            existing_team = await self.repository.get_by_name(team_update.name)
            if existing_team:
                raise DuplicateEntityException(
                    key="team.name_exists", params={"name": team_update.name}
                )

        update_data = team_update.model_dump(exclude_unset=True)
        update_data = Team.add_audit_info(update_data, current_user.id)
        return await self.repository.update(id, update_data)

    async def get_all_teams(self) -> List[Team]:
        return await self.repository.get_all()

    async def delete_team(self, id: int, current_user: UserRead) -> bool:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise PermissionDeniedException(
                params={"detail": "team.delete_permission_denied"}
            )
        deleted = await self.repository.delete(id)
        if not deleted:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": id}
            )
        return True


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_team_service(session: SessionDep, settings: SettingsDep) -> TeamService:
    repo = TeamRepository(session, Team)
    return TeamService(repo, settings)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
