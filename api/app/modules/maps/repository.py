from typing import Any, List, Optional

from sqlmodel import or_, select

from app.core.enums.access_policy import AccessPolicy
from app.core.repository import BaseRepository
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.maps.models import Map


class MapRepository(BaseRepository[Map]):
    """Repository for Map entities."""

    async def get_all(
        self,
        options: Optional[List[Any]] = None,
        filter_owner_id: Optional[int] = None,
        filter_team_ids: Optional[List[int]] = None,
        admin_bypass: bool = False,
    ) -> List[Map]:
        query = select(Map).distinct()
        query_options = self.get_load_options() if options is None else options
        for option in query_options:
            query = query.options(option)

        if admin_bypass:
            pass
        else:
            # Join for Atlas and TeamLink checks
            if filter_team_ids or filter_owner_id:
                query = query.join(Atlas)

            if filter_team_ids:
                query = query.outerjoin(
                    AtlasTeamLink, Atlas.id == AtlasTeamLink.atlas_id
                )

            conditions = []
            conditions.append(Map.access_policy == AccessPolicy.PUBLIC)

            if filter_owner_id:
                # User sees maps they created OR maps in Atlases they created
                conditions.append(Map.created_by_id == filter_owner_id)
                conditions.append(Atlas.created_by_id == filter_owner_id)

            if filter_team_ids:
                # User sees maps if they are in a team linked to the map's atlas
                conditions.append(AtlasTeamLink.team_id.in_(filter_team_ids))

            if conditions:
                query = query.where(or_(*conditions))
            else:
                query = query.where(Map.id == -1)

        result = await self.session.exec(query)
        return list(result.all())

    async def get_by_atlas_and_name(self, atlas_id: int, name: str) -> Map | None:
        """Get a map by atlas_id and name."""
        query = select(Map).where(Map.atlas_id == atlas_id, Map.name == name)
        result = await self.session.exec(query)
        return result.first()
