from typing import TYPE_CHECKING, Optional

from sqlmodel import TEXT, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.atlases.models import Atlas


class Map(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = Field(sa_column=Column(TEXT))
    style: str
    atlas_id: int = Field(foreign_key="atlas.id")
    atlas: "Atlas" = Relationship(back_populates="maps")
