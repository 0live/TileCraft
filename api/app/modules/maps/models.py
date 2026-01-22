from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlmodel import TEXT, Column, Field, Relationship, SQLModel, UniqueConstraint

from app.core.mixins.audit_mixin import AuditMixin

if TYPE_CHECKING:
    from app.modules.atlases.models import Atlas


class Map(AuditMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = Field(sa_column=Column(TEXT))
    style: str
    atlas_id: int = Field(sa_column=Column(ForeignKey("atlas.id", ondelete="CASCADE")))
    atlas: "Atlas" = Relationship(back_populates="maps")

    __table_args__ = (UniqueConstraint("atlas_id", "name", name="uix_map_atlas_name"),)
