from typing import TYPE_CHECKING, List, Optional

from sqlmodel import TEXT, Column, Field, Relationship, SQLModel

from app.modules.maps.models import AtlasMapLink, Map

if TYPE_CHECKING:
    from app.modules.teams.models import Team


class AtlasTeamLink(SQLModel, table=True):
    atlas_id: int = Field(foreign_key="atlas.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    can_manage_atlas: bool = False
    can_create_maps: bool = False
    can_edit_maps: bool = False


class Atlas(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = Field(sa_column=Column(TEXT))
    teams: List["Team"] = Relationship(
        back_populates="atlases", link_model=AtlasTeamLink
    )
    maps: List["Map"] = Relationship(back_populates="atlases", link_model=AtlasMapLink)
