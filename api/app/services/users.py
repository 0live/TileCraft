from typing import Optional
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlmodel import select

from app.db.users import User
from app.core.database import SessionDep
from app.models.users import UserCreate, UserRead
from app.services.auth import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(user: UserCreate, session: SessionDep) -> UserRead:
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.model_dump()
    user_dict.pop("password")
    user = User(**user_dict, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_email(session: SessionDep, email: str) -> Optional[UserRead]:
    result = session.exec(select(User).where(User.email == email))
    return result.first()


def authenticate_user(session: SessionDep, email: str, password: str) -> Optional[str]:
    user = get_user_by_email(session, email)
    if user and pwd_context.verify(password, user.hashed_password):
        token = create_access_token(data={"sub": email})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
