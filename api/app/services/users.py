from typing import Annotated, Optional
from fastapi import HTTPException, status, Depends
from sqlmodel import select

from app.db.users import User
from app.core.database import SessionDep
from app.models.users import UserCreate, UserRead
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
    user_dict = user.model_dump(exclude={"password"})
    new_user = User(**user_dict, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserRead(**new_user.model_dump())


def get_user_by_username(session: SessionDep, username: str) -> Optional[User]:
    result = session.exec(select(User).where(User.username == username))
    return result.first()


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
