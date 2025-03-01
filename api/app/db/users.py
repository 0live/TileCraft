from pydantic import EmailStr
from sqlmodel import ARRAY, Column, Relationship, SQLModel, Field
from typing import List, Optional
from app.db.teams import Team, UserTeamLink
from app.models.user_roles import UserRole
from sqlalchemy import Enum as SAEnum


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    roles: List[UserRole] = Field(sa_column=Column(ARRAY(SAEnum(UserRole))))
    teams: list[Team] = Relationship(back_populates="heroes", link_model=UserTeamLink)
