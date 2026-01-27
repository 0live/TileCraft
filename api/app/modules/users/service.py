from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.exceptions import (
    AuthenticationException,
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.core.messages import MessageService
from app.core.security import (
    get_token,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import Token
from app.modules.teams.models import Team
from app.modules.teams.service import TeamService
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserDetail, UserSummary, UserUpdate


class UserService:
    """Service for user CRUD operations (not authentication)."""

    def __init__(
        self,
        repository: UserRepository,
        team_service: TeamService,
        settings: Settings,
    ):
        self.repository = repository
        self.team_service = team_service
        self.settings = settings

    async def create_user(self, user: UserCreate) -> UserDetail:
        """Create a new user (used for testing, prefer auth/register for production)."""
        # Check email uniqueness
        existing_email_user = await self.repository.get_by_email(user.email)
        if existing_email_user:
            raise DuplicateEntityException(
                key="user.email_exists", params={"email": user.email}
            )

        existing_username = await self.repository.get_by_username(user.username)
        if existing_username:
            raise DuplicateEntityException(
                key="user.username_exists", params={"username": user.username}
            )

        hashed_pw = hash_password(user.password)
        user_data = user.model_dump(exclude={"password", "roles", "teams"})
        user_data["hashed_password"] = hashed_pw
        user_data["roles"] = [UserRole.USER]

        new_user = await self.repository.create(user_data)
        await self.repository.session.commit()

        return await self.repository.get(
            new_user.id, options=[selectinload(User.teams).selectinload(Team.users)]
        )

    async def get_all_users(self, current_user: UserDetail) -> list[UserSummary]:
        if UserRole.ADMIN not in current_user.roles:
            raise PermissionDeniedException(
                params={"detail": "user.list_permission_denied"}
            )
        return await self.repository.get_all()

    async def get_user_by_id(
        self, user_id: int, current_user: UserDetail
    ) -> UserDetail:
        if UserRole.ADMIN not in current_user.roles and current_user.id != user_id:
            raise PermissionDeniedException(
                params={"detail": "user.read_permission_denied"}
            )

        user = await self.repository.get(
            user_id, options=[selectinload(User.teams).selectinload(Team.users)]
        )
        if not user:
            raise EntityNotFoundException(
                entity="User", key="user.not_found", params={"id": user_id}
            )
        return user

    async def get_by_username(
        self, username: str, with_relations: bool = False
    ) -> Optional[User]:
        options = []
        if with_relations:
            options = [selectinload(User.teams).selectinload(Team.users)]
        return await self.repository.get_by_username(username, options=options)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.repository.get_by_email(email)

    async def authenticate_user(self, username: str, password: str) -> Optional[Token]:
        """Authenticate a user (kept for backwards compatibility)."""
        user = await self.repository.get_by_username(
            username, options=[selectinload(User.teams).selectinload(Team.users)]
        )
        if user and verify_password(password, user.hashed_password):
            return get_token(UserDetail.model_validate(user), settings=self.settings)
        raise AuthenticationException()

    async def delete_user(self, user_id: int, current_user: UserDetail) -> bool:
        if UserRole.ADMIN not in current_user.roles:
            raise PermissionDeniedException(
                params={"detail": "user.delete_permission_denied"}
            )
        deleted = await self.repository.delete(user_id)
        await self.repository.session.commit()
        if not deleted:
            raise EntityNotFoundException(
                entity="User", key="user.not_found", params={"id": user_id}
            )
        return {"message": MessageService.get_message("user.deleted_success")}

    async def update_user(
        self, user_id: int, user_update: UserUpdate, current_user: UserDetail
    ) -> UserDetail:
        if user_id != current_user.id and UserRole.ADMIN not in current_user.roles:
            raise PermissionDeniedException(
                params={"detail": "user.update_permission_denied"}
            )

        update_data = user_update.model_dump(
            exclude_unset=True, exclude={"password", "roles", "teams"}
        )

        if user_update.password is not None:
            hashed_password = hash_password(user_update.password)
            update_data["hashed_password"] = hashed_password

        if user_update.roles is not None:
            if UserRole.ADMIN not in current_user.roles:
                raise PermissionDeniedException(
                    params={"detail": "user.role_permission_denied"}
                )
            update_data["roles"] = user_update.roles

        if user_update.teams is not None:
            if all(
                role not in current_user.roles
                for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
            ):
                raise PermissionDeniedException(
                    params={"detail": "user.team_permission_denied"}
                )

            teams_to_link = []
            for team_id in user_update.teams:
                team = await self.team_service.get_team_by_id(team_id, current_user)
                teams_to_link.append(team)

            update_data["teams"] = teams_to_link

        await self.repository.update(
            user_id, update_data, options=[selectinload(User.teams)]
        )
        await self.repository.session.commit()

        return await self.repository.get(
            user_id, options=[selectinload(User.teams).selectinload(Team.users)]
        )


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_user_service(session: SessionDep, settings: SettingsDep) -> UserService:
    repo = UserRepository(session, User)
    from app.modules.teams.service import get_team_service

    team_service = get_team_service(session, settings)
    return UserService(repo, team_service, settings)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
