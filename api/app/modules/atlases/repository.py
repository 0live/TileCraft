from typing import Any, List, Optional

from sqlmodel import or_, select

from app.core.enums.access_policy import AccessPolicy
from app.core.repository import BaseRepository
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.teams.models import Team


class AtlasRepository(BaseRepository[Atlas]):
    """Repository for Atlas entities."""

    async def get_all(
        self,
        options: Optional[List[Any]] = None,
        filter_owner_id: Optional[int] = None,
        filter_team_ids: Optional[List[int]] = None,
        admin_bypass: bool = False,
    ) -> List[Atlas]:
        """
        Get all atlases with explicit filters.
        """
        query = select(Atlas).distinct()
        if options:
            for option in options:
                query = query.options(option)

        if admin_bypass:
            pass
        else:
            # We need to join if we filter by team membership
            if filter_team_ids:
                query = query.outerjoin(AtlasTeamLink)

            conditions = []
            conditions.append(Atlas.access_policy == AccessPolicy.PUBLIC)
            if filter_owner_id:
                conditions.append(Atlas.created_by_id == filter_owner_id)
            if filter_team_ids:
                conditions.append(AtlasTeamLink.team_id.in_(filter_team_ids))

            if conditions:
                query = query.where(or_(*conditions))
            else:
                # Safety: If not admin_bypass and no other criteria, return nothing.
                query = query.where(Atlas.id == -1)

        result = await self.session.exec(query)
        return list(result.all())

    async def get_team_link(
        self, atlas_id: int, team_id: int
    ) -> Optional[AtlasTeamLink]:
        """
        Get a link between an atlas and a team.
        """
        statement = select(AtlasTeamLink).where(
            AtlasTeamLink.atlas_id == atlas_id,
            AtlasTeamLink.team_id == team_id,
        )
        result = await self.session.exec(statement)
        return result.first()

    async def create_team_link(self, link_data: dict) -> AtlasTeamLink:
        """
        Create a link between an atlas and a team.
        """
        # Ensure team exists
        team_id = link_data.get("team_id")
        team_result = await self.session.exec(select(Team).where(Team.id == team_id))
        if not team_result.first():
            raise ValueError("Team not found")

        new_link = AtlasTeamLink(**link_data)
        self.session.add(new_link)
        await self.session.flush()
        return new_link

    async def update_team_link(
        self, link: AtlasTeamLink, update_data: dict
    ) -> AtlasTeamLink:
        """
        Update a link between an atlas and a team.
        """
        for key, value in update_data.items():
            setattr(link, key, value)
        self.session.add(link)
        await self.session.flush()
        return link

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
        await self.session.flush()
        return True
