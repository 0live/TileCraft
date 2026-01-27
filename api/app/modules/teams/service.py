from typing import Annotated, List

from fastapi import Depends
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.enums.access_policy import AccessPolicy
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.teams.models import Team
from app.modules.teams.repository import TeamRepository
from app.modules.teams.schemas import (
    TeamBase,
    TeamDetail,
    TeamSummary,
)
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail


class TeamService:
    def __init__(self, repository: TeamRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def create_team(self, team: TeamBase, current_user: UserDetail) -> TeamDetail:
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

        team_obj = await self.repository.create(team_data)
        await self.repository.session.commit()

        return await self.repository.get(
            team_obj.id, options=[selectinload(Team.users)]
        )

    async def get_all_teams(self, current_user: UserDetail) -> List[TeamSummary]:
        can_view_all = any(
            role in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        )
        return await self.repository.get_all(
            user=current_user, filter_by_access=not can_view_all
        )

    async def get_team_by_id(self, id: int, current_user: UserDetail) -> TeamDetail:
        team = await self.repository.get(id, options=[selectinload(Team.users)])
        if not team:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": id}
            )

        can_view = (
            any(
                role in current_user.roles
                for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
            )
            or team.created_by_id == current_user.id
            or team.access_policy == AccessPolicy.PUBLIC
            or any(user.id == current_user.id for user in team.users)
        )

        if not can_view:
            raise PermissionDeniedException(
                params={"detail": "team.view_permission_denied"}
            )

        return team

    async def update_team(
        self, id: int, team_update: TeamBase, current_user: UserDetail
    ) -> TeamDetail:
        team = await self.repository.get(id)
        if not team:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": id}
            )

        can_edit = any(
            role in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        )

        if not can_edit:
            raise PermissionDeniedException(
                params={"detail": "team.update_permission_denied"}
            )

        if team_update.name != team.name:
            existing_team = await self.repository.get_by_name(team_update.name)
            if existing_team:
                raise DuplicateEntityException(
                    key="team.name_exists", params={"name": team_update.name}
                )

        update_data = team_update.model_dump(exclude_unset=True)
        update_data = Team.add_audit_info(update_data, current_user.id)

        await self.repository.update(id, update_data)
        await self.repository.session.commit()

        # Return detail
        return await self.repository.get(id, options=[selectinload(Team.users)])

    async def delete_team(self, id: int, current_user: UserDetail) -> bool:
        team = await self.repository.get(id)
        if not team:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": id}
            )

        can_delete = any(
            role in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        )

        if not can_delete:
            raise PermissionDeniedException(
                params={"detail": "team.delete_permission_denied"}
            )

        deleted = await self.repository.delete(id)
        if not deleted:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": id}
            )
        await self.repository.session.commit()
        return True

    async def add_member(
        self, team_id: int, user_id: int, current_user: UserDetail
    ) -> TeamDetail:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise PermissionDeniedException(
                params={"detail": "team.update_permission_denied"}
            )

        team = await self.repository.get(team_id, options=[selectinload(Team.users)])
        if not team:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": team_id}
            )

        # Use session.get to avoid importing UserRepository and creating circular dep
        from app.modules.users.models import User

        user = await self.repository.session.get(User, user_id)
        if not user:
            raise EntityNotFoundException(
                entity="User", key="user.not_found", params={"id": user_id}
            )

        if user not in team.users:
            team.users.append(user)
            await self.repository.session.commit()
            await self.repository.session.refresh(team)

        return team

    async def remove_member(
        self, team_id: int, user_id: int, current_user: UserDetail
    ) -> TeamDetail:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise PermissionDeniedException(
                params={"detail": "team.update_permission_denied"}
            )

        team = await self.repository.get(team_id, options=[selectinload(Team.users)])
        if not team:
            raise EntityNotFoundException(
                entity="Team", key="team.not_found", params={"id": team_id}
            )

        user_to_remove = next((u for u in team.users if u.id == user_id), None)
        if not user_to_remove:
            raise EntityNotFoundException(
                entity="User", key="team.user_not_found", params={"id": user_id}
            )

        team.users.remove(user_to_remove)
        await self.repository.session.commit()
        await self.repository.session.refresh(team)

        return team


# Dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_team_service(session: SessionDep, settings: SettingsDep) -> TeamService:
    repo = TeamRepository(session, Team)
    return TeamService(repo, settings)


TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
