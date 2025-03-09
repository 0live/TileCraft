from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlmodel import Field


class AtlasInMap(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MapBase(BaseModel):
    name: str
    description: str
    style: str
    atlases: List[AtlasInMap]
    model_config = ConfigDict(from_attributes=True)


class MapRead(MapBase):
    id: int


class MapUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    style: Optional[str] = Field(default=None)
    atlases: Optional[List[int]] = Field(default=None)
