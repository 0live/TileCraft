from typing import TYPE_CHECKING, Optional, List
from sqlmodel import Field, SQLModel, Relationship
from app.db.atlases import Atlas, AtlasTeamLink

if TYPE_CHECKING:
    from app.db.users import User


class UserTeamLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    users: List["User"] = Relationship(back_populates="teams", link_model=UserTeamLink)
    atlases: List["Atlas"] = Relationship(
        back_populates="teams", link_model=AtlasTeamLink
    )
