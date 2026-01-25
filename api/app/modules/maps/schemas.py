from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field


class MapBase(BaseModel):
    name: str
    description: str
    atlas_id: int
    model_config = ConfigDict(from_attributes=True)


class MapCreate(MapBase):
    style: str


class MapSummary(MapBase):
    id: int


class MapDetail(MapSummary):
    id: int
    style: str


class MapUpdate(BaseModel):
    atlas_id: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    style: Optional[str] = Field(default=None)
