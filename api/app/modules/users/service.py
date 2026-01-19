from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlmodel import select

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
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate


class UserService:
    """Service for user CRUD operations (not authentication)."""

    def __init__(self, repository: UserRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def create_user(self, user: UserCreate) -> UserRead:
        """Create a new user (used for testing, prefer auth/register for production)."""
        existing_email = await self.repository.session.exec(
            select(User).where(User.email == user.email)
        )
        if existing_email.first():
            raise HTTPException(status_code=400, detail="Email already registered")

        existing_username = await self.repository.get_by_username(user.username)
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_pw = hash_password(user.password)
        user_data = user.model_dump(exclude={"password", "roles", "teams"})
        user_data["hashed_password"] = hashed_pw
        user_data["roles"] = [UserRole.USER]

        new_user = await self.repository.create(user_data)
        return await self.get_by_username(new_user.username)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.repository.get_by_username(username)

    async def authenticate_user(self, username: str, password: str) -> Optional[Token]:
        """Authenticate a user (kept for backwards compatibility)."""
        user = await self.get_by_username(username)
        if user and verify_password(password, user.hashed_password):
            return get_token(UserRead.model_validate(user), settings=self.settings)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    async def update_user(
        self, user_id: int, user_update: UserUpdate, current_user: UserRead
    ) -> UserRead:
        if user_id != current_user.id and UserRole.ADMIN not in current_user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        user_db = await self.repository.get_with_teams(user_id)
        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        user_dict = user_update.model_dump(
            exclude_unset=True, exclude={"password", "roles", "teams"}
        )

        if user_update.password is not None:
            hashed_password = hash_password(user_update.password)
            user_dict.update({"hashed_password": hashed_password})

        if user_update.roles is not None:
            if UserRole.ADMIN not in current_user.roles:
                raise HTTPException(
                    status_code=403, detail="Only admin can change roles"
                )
            user_dict["roles"] = user_update.roles

        if user_update.teams is not None:
            if all(
                role not in current_user.roles
                for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
            ):
                raise HTTPException(
                    status_code=403, detail="You don't have permission to change teams"
                )

            current_team_ids = {t.id for t in user_db.teams}
            for team_id in user_update.teams:
                if team_id in current_team_ids:
                    team_to_remove = next(t for t in user_db.teams if t.id == team_id)
                    user_db.teams.remove(team_to_remove)
                else:
                    team_result = await self.repository.session.exec(
                        select(Team).where(Team.id == team_id)
                    )
                    team = team_result.first()
                    if team:
                        user_db.teams.append(team)
                    else:
                        raise HTTPException(status_code=404, detail="Team not found")

        for key, value in user_dict.items():
            setattr(user_db, key, value)

        self.repository.session.add(user_db)
        await self.repository.session.commit()
        await self.repository.session.refresh(user_db)

        return await self.update_user_reload(user_db.id)

    async def update_user_reload(self, user_id: int) -> UserRead:
        user_db = await self.repository.get_with_teams(user_id)
        return UserRead.model_validate(user_db)


# =============================================================================
# Dependencies
# =============================================================================

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_user_service(session: SessionDep, settings: SettingsDep) -> UserService:
    repo = UserRepository(session, User)
    return UserService(repo, settings)


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
