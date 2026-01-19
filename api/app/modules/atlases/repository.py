from typing import Any, List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.teams.models import Team


class AtlasRepository(BaseRepository[Atlas]):
    """Repository for Atlas entities with eager loading of teams and maps relationships."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(Atlas.teams), selectinload(Atlas.maps)]

    async def get_by_name(self, name: str) -> Optional[Atlas]:
        """Get an atlas by name with relations loaded."""
        from sqlmodel import select

        query = select(self.model).where(self.model.name == name)
        for option in self.get_load_options():
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def upsert_team_link(self, link_data: dict) -> AtlasTeamLink:
        """
        Create or update a link between an atlas and a team.
        """
        # Ensure team exists
        team_id = link_data.get("team_id")
        team_result = await self.session.exec(select(Team).where(Team.id == team_id))
        if not team_result.first():
            raise ValueError("Team not found")

        atlas_id = link_data.get("atlas_id")
        existing_link_result = await self.session.exec(
            select(AtlasTeamLink).where(
                AtlasTeamLink.atlas_id == atlas_id,
                AtlasTeamLink.team_id == team_id,
            )
        )
        existing_link = existing_link_result.first()

        if existing_link:
            for key, value in link_data.items():
                setattr(existing_link, key, value)
            self.session.add(existing_link)
            await self.session.commit()
            await self.session.refresh(existing_link)
            return existing_link
        else:
            new_link = AtlasTeamLink(**link_data)
            self.session.add(new_link)
            await self.session.commit()
            await self.session.refresh(new_link)
            return new_link

    async def delete_team_link(self, atlas_id: int, team_id: int) -> bool:
        """Delete a link between an atlas and a team."""
        link_result = await self.session.exec(
            select(AtlasTeamLink).where(
                AtlasTeamLink.atlas_id == atlas_id,
                AtlasTeamLink.team_id == team_id,
            )
        )
        link = link_result.first()
        if not link:
            return False

        await self.session.delete(link)
        await self.session.commit()
        return True
