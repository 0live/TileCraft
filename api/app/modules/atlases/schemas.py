from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field

from app.core.enums.access_policy import AccessPolicy


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
    access_policy: Optional[AccessPolicy] = Field(default=None)

    teams: Optional[List[int]] = Field(default=None)


class AtlasTeamLinkRead(BaseModel):
    atlas_id: int
    team_id: int
    can_manage_atlas: bool
    can_create_maps: bool
    can_edit_maps: bool


class AtlasTeamLinkCreate(BaseModel):
    atlas_id: int
    team_id: int
    can_manage_atlas: Optional[bool] = Field(default=False)
    can_create_maps: Optional[bool] = Field(default=False)
    can_edit_maps: Optional[bool] = Field(default=False)
