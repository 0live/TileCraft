from enum import Enum
from typing import List, Optional

from pydantic import EmailStr
from sqlalchemy import Enum as SAEnum
from sqlmodel import ARRAY, Column, Field, Relationship, SQLModel

from app.modules.teams.models import Team, UserTeamLink


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    MANAGE_TEAMS = "MANAGE_TEAMS"
    MANAGE_ATLASES_AND_MAPS = "MANAGE_ATLASES_AND_MAPS"
    LOAD_DATA = "LOAD_DATA"
    LOAD_ICONS = "LOAD_ICONS"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    roles: List[UserRole] = Field(sa_column=Column(ARRAY(SAEnum(UserRole))))
    teams: List["Team"] = Relationship(back_populates="users", link_model=UserTeamLink)
