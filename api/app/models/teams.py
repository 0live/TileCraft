from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class TeamRead(TeamBase):
    id: int
