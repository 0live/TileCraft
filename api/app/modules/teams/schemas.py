from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr


class UserInTeam(BaseModel):
    id: int
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class TeamBase(BaseModel):
    name: str
    users: List[UserInTeam] = []
    model_config = ConfigDict(from_attributes=True)


class TeamRead(TeamBase):
    id: int


class TeamUpdate(BaseModel):
    name: str | None = None
    users: List[UserInTeam] | None = None
    model_config = ConfigDict(from_attributes=True)
