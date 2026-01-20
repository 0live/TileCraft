from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings, get_settings
from app.core.database import SessionDep
from app.core.security import (
    decode_token,
    get_token,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from app.modules.auth.schemas import Token
from app.modules.teams.models import Team
from app.modules.teams.repository import TeamRepository as TeamRepoDependency
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate


class UserService:
    """Service for user CRUD operations (not authentication)."""

    def __init__(
        self,
        repository: UserRepository,
        team_repository: TeamRepoDependency,
        settings: Settings,
    ):
        self.repository = repository
        self.team_repository = team_repository
        self.settings = settings

    async def create_user(self, user: UserCreate) -> UserRead:
        """Create a new user (used for testing, prefer auth/register for production)."""
        # Check email uniqueness
        # Although repository create might catch integrity error, explicit check is often better for error msgs
        existing_email_user = await self.repository.get_by_email(user.email)
        if existing_email_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        existing_username = await self.repository.get_by_username(user.username)
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_pw = hash_password(user.password)
        user_data = user.model_dump(exclude={"password", "roles", "teams"})
        user_data["hashed_password"] = hashed_pw
        user_data["roles"] = [UserRole.USER]

        # Use repository create
        new_user = await self.repository.create(user_data)

        # We can return this directly as repository.create now reloads relations
        return UserRead.model_validate(new_user)

    async def get_all_users(self) -> list[User]:
        return await self.repository.get_all()

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self.repository.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.repository.get_by_username(username)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.repository.get_by_email(email)

    async def authenticate_user(self, username: str, password: str) -> Optional[Token]:
        """Authenticate a user (kept for backwards compatibility)."""
        user = await self.get_by_username(username)
        if user and verify_password(password, user.hashed_password):
            return get_token(UserRead.model_validate(user), settings=self.settings)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    async def delete_user(self, user_id: int) -> bool:
        return await self.repository.delete(user_id)

    async def update_user(
        self, user_id: int, user_update: UserUpdate, current_user: UserRead
    ) -> UserRead:
        if user_id != current_user.id and UserRole.ADMIN not in current_user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Prepare update dictionary
        update_data = user_update.model_dump(
            exclude_unset=True, exclude={"password", "roles", "teams"}
        )

        if user_update.password is not None:
            hashed_password = hash_password(user_update.password)
            update_data["hashed_password"] = hashed_password

        if user_update.roles is not None:
            if UserRole.ADMIN not in current_user.roles:
                raise HTTPException(
                    status_code=403, detail="Only admin can change roles"
                )
            # Ensure roles is a list
            update_data["roles"] = user_update.roles

        # Handle teams relationship
        if user_update.teams is not None:
            if all(
                role not in current_user.roles
                for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
            ):
                raise HTTPException(
                    status_code=403, detail="You don't have permission to change teams"
                )

            # Fetch team objects
            teams_to_link = []
            for team_id in user_update.teams:
                team = await self.team_repository.get(team_id)
                if not team:
                    raise HTTPException(
                        status_code=404, detail=f"Team {team_id} not found"
                    )
                teams_to_link.append(team)

            # We can't easily pass list of objects to 'update' via dict if we rely on
            # Pydantic or SQLModel automatic handling usually expects IDs for foreign keys,
            # but for Many-to-Many via SQLModel Relationship, we often need to set the list of objects on the instance.
            # The BaseRepository.update takes a dict and does setattr.
            # setattr(user_db, "teams", teams_to_link) will work for SQLAlchemy relationships.
            update_data["teams"] = teams_to_link

        # Use repository update
        # Since we might have complex objects in update_data (teams list),
        # let's verify BaseRepository.update handles it.
        # BaseRepository.update: for key, value in attributes.items(): setattr(db_obj, key, value)
        # This works perfectly for SA relationships.
        updated_user = await self.repository.update(user_id, update_data)
        return UserRead.model_validate(updated_user)


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_user_service(session: SessionDep, settings: SettingsDep) -> UserService:
    repo = UserRepository(session, User)
    team_repo = TeamRepoDependency(session, Team)
    return UserService(repo, team_repo, settings)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: UserServiceDep,
) -> UserRead:
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, settings=service.settings)
        username = payload.get("username")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await service.get_by_username(username)
    if user is None:
        raise credentials_exception
    return UserRead.model_validate(user)
