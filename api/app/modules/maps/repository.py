from app.core.repository import BaseRepository
from app.modules.maps.models import Map


class MapRepository(BaseRepository[Map]):
    """Repository for Map entities."""
