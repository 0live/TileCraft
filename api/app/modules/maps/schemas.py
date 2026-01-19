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
    model_config = ConfigDict(from_attributes=True)


class MapCreate(MapBase):
    atlases: Optional[List[int]] = []


class MapRead(MapBase):
    id: int
    atlases: List[AtlasInMap] = []


class MapUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    style: Optional[str] = Field(default=None)
    atlases: Optional[List[int]] = Field(default=None)
