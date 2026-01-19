from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field


class MapBase(BaseModel):
    name: str
    description: str
    style: str
    model_config = ConfigDict(from_attributes=True)


class MapCreate(MapBase):
    atlas_id: int


class MapRead(MapBase):
    id: int
    atlas_id: int


class MapUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    style: Optional[str] = Field(default=None)
