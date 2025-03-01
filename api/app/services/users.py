from typing import Annotated, Optional
from fastapi import HTTPException, status, Depends
from sqlmodel import select

from app.db.teams import Team
from app.models.user_roles import UserRole
from app.db.users import User
from app.core.database import SessionDep
from app.models.users import UserCreate, UserRead, UserUpdate
from app.services.auth.auth import (
    create_access_token,
    pwd_context,
    oauth2_scheme,
    decode_token,
)
from app.models.auth import Token
from jwt.exceptions import InvalidTokenError


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
    print(user)
    return user


def authenticate_user(
    session: SessionDep, username: str, password: str
) -> Optional[Token]:
    user: Optional[User] = get_user_by_username(session, username)
    if user and pwd_context.verify(password, user.hashed_password):
        token = create_access_token(data={"sub": username})
        return Token(access_token=token, token_type="bearer")
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
    return UserRead(**user.model_dump())


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
        teams = session.exec(select(Team).where(Team.id.in_(user.teams))).all()  # type: ignore
        user_db.teams = list(teams)

    for key, value in user_dict.items():
        setattr(user_db, key, value)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return UserRead(**user_db.model_dump(exclude={"hashed_password"}))
