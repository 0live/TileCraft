from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey
from sqlmodel import Column, Field, Relationship, SQLModel

from app.core.mixins.audit_mixin import AuditMixin
from app.modules.atlases.models import Atlas, AtlasTeamLink

if TYPE_CHECKING:
    from app.modules.users.models import User


class UserTeamLink(SQLModel, table=True):
    user_id: int = Field(
        sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    )
    team_id: int = Field(
        sa_column=Column(ForeignKey("team.id", ondelete="CASCADE"), primary_key=True)
    )


class Team(AuditMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    users: List["User"] = Relationship(
        back_populates="teams",
        link_model=UserTeamLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )
    atlases: List["Atlas"] = Relationship(
        back_populates="teams",
        link_model=AtlasTeamLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )
