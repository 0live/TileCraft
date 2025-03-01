from pydantic import BaseModel


class TeamBase(BaseModel):
    name: str


class TeamRead(TeamBase):
    id: int
