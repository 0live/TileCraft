from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey
from sqlmodel import TEXT, Column, Field, Relationship, SQLModel

from app.core.mixins.audit_mixin import AuditMixin
from app.modules.maps.models import Map

if TYPE_CHECKING:
    from app.modules.teams.models import Team


class AtlasTeamLink(SQLModel, table=True):
    atlas_id: int = Field(
        sa_column=Column(ForeignKey("atlas.id", ondelete="CASCADE"), primary_key=True)
    )
    team_id: int = Field(
        sa_column=Column(ForeignKey("team.id", ondelete="CASCADE"), primary_key=True)
    )
    can_manage_atlas: bool = False
    can_create_maps: bool = False
    can_edit_maps: bool = False


class Atlas(AuditMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str = Field(sa_column=Column(TEXT))
    teams: List["Team"] = Relationship(
        back_populates="atlases",
        link_model=AtlasTeamLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )
    maps: List["Map"] = Relationship(
        back_populates="atlas",
        sa_relationship_kwargs={"passive_deletes": True},
    )
