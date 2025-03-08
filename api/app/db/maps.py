from typing import TYPE_CHECKING, List, Optional
from sqlmodel import TEXT, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.atlases import Atlas


class AtlasMapLink(SQLModel, table=True):
    atlas_id: int = Field(foreign_key="atlas.id", primary_key=True)
    map_id: int = Field(foreign_key="map.id", primary_key=True)


class Map(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = Field(sa_column=Column(TEXT))
    style: str
    atlases: List["Atlas"] = Relationship(
        back_populates="maps", link_model=AtlasMapLink
    )
