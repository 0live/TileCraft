from typing import Any, List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import or_, select

from app.core.enums.access_policy import AccessPolicy
from app.core.repository import BaseRepository
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.teams.models import Team


class AtlasRepository(BaseRepository[Atlas]):
    """Repository for Atlas entities with eager loading of teams and maps relationships."""

    def get_load_options(self) -> List[Any]:
        return [selectinload(Atlas.teams), selectinload(Atlas.maps)]

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
        query_options = self.get_load_options() if options is None else options
        for option in query_options:
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
