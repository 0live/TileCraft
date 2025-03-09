import secrets
from typing import Annotated, Optional
from fastapi import HTTPException, Request, status, Depends
from sqlmodel import select

from app.db.teams import Team
from app.models.user_roles import UserRole
from app.db.users import User
from app.core.database import SessionDep
from app.models.users import UserCreate, UserRead, UserUpdate
from app.services.auth.auth import (
    get_token,
    pwd_context,
    oauth2_scheme,
    decode_token,
)
from app.models.auth import Token
from jwt.exceptions import InvalidTokenError
from app.services.auth import oauth


def create_user(user: UserCreate, session: SessionDep) -> Optional[UserRead]:
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if session.exec(select(User).where(User.username == user.username)).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = pwd_context.hash(user.password)
    user_dict = user.model_dump(exclude={"password", "roles", "teams"})
    new_user = User(**user_dict, roles=[UserRole.USER], hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserRead(**new_user.model_dump())


def get_user_by_username(session: SessionDep, username: str) -> Optional[User]:
    result = session.exec(select(User).where(User.username == username))
    user = result.first()
    return user


def authenticate_user(
    session: SessionDep, username: str, password: str
) -> Optional[Token]:
    user: Optional[User] = get_user_by_username(session, username)
    if user and pwd_context.verify(password, user.hashed_password):
        return get_token(username)
    raise HTTPException(status_code=401, detail="Invalid credentials")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user_by_username(session, username)
    if user is None:
        raise credentials_exception
    return UserRead.model_validate(user)


def update_user(
    user_id: int,
    user: UserUpdate,
    session: SessionDep,
    current_user: UserRead,
) -> Optional[UserRead]:
    if user_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    user_db = session.exec(select(User).where(User.id == user_id)).first()

    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    user_dict = user.model_dump(
        exclude_unset=True, exclude={"password", "roles", "teams"}
    )

    if user.password is not None:
        hashed_password = pwd_context.hash(user.password)
        user_dict.update({"hashed_password": hashed_password})

    if user.roles is not None:
        if UserRole.ADMIN not in current_user.roles:
            raise HTTPException(status_code=403, detail="Only admin can change roles")
        user_dict["roles"] = user.roles

    if user.teams is not None:
        if all(
            role not in current_user.roles
            for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
        ):
            raise HTTPException(
                status_code=403, detail="You don't have permission to change teams"
            )
        for team_id in user.teams:
            team = session.exec(select(Team).where(Team.id == team_id)).first()
            if team:
                user_db.teams.append(team)
            else:
                raise HTTPException(status_code=404, detail="Team not found")

    for key, value in user_dict.items():
        setattr(user_db, key, value)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return UserRead.model_validate(user_db)


async def manage_google_user(request: Request, session: SessionDep):
    if not oauth.google:
        raise HTTPException(status_code=502, detail="Google OAuth configuration failed")

    auth_result = await oauth.google.authorize_access_token(request)
    user = auth_result.get("userinfo")
    email = user.get("email")

    if not user or not user.email:
        raise HTTPException(status_code=502, detail="Google OAuth data parsing failed")

    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        return get_token(existing_user.username)
    if not existing_user:
        user_data = {
            "email": email,
            "username": user.get("name") or email.split("@")[0],
        }
        hashed_password = pwd_context.hash(secrets.token_urlsafe(15))
        new_user = User(
            **user_data, roles=[UserRole.USER], hashed_password=hashed_password
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        existing_user = new_user
        return get_token(new_user.username)

    raise HTTPException(status_code=500, detail="Error on Google Authentication")
