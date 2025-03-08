from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlmodel import Field


class TeamInAtlas(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MapInAtlas(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class AtlasBase(BaseModel):
    name: str
    description: str
    teams: List[TeamInAtlas] = []
    maps: List[MapInAtlas] = []
    model_config = ConfigDict(from_attributes=True)


class AtlasRead(AtlasBase):
    id: int


class AtlasUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    teams: Optional[List[int]] = Field(default=None)
    maps: Optional[List[int]] = Field(default=None)
