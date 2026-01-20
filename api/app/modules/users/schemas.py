from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.teams.schemas import TeamRead
from app.modules.users.models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    roles: List[UserRole] = [UserRole.USER]
    teams: List[TeamRead] = []
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(default=None)
    username: Optional[str] = Field(default=None)
    roles: Optional[List[UserRole]] = Field(default=None)
    password: Optional[str] = Field(default=None)
    teams: Optional[List[int]] = Field(default=None)
