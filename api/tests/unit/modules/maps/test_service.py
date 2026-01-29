from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.enums.access_policy import AccessPolicy
from app.core.exceptions import EntityNotFoundException, PermissionDeniedException
from app.modules.maps.schemas import MapCreate, MapUpdate
from app.modules.maps.service import MapService
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail


class TestMapService:
    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        repo.session = AsyncMock()
        return repo

    @pytest.fixture
    def mock_settings(self):
        return Settings()

    @pytest.fixture
    def service(self, mock_repo, mock_settings):
        return MapService(
            repository=mock_repo,
            settings=mock_settings,
        )

    @pytest.fixture
    def admin_user(self):
        return UserDetail(
            id=1,
            username="admin",
            email="admin@test.com",
            roles=[UserRole.ADMIN],
            teams=[],
        )

    @pytest.fixture
    def user(self):
        return UserDetail(
            id=2,
            username="user",
            email="user@test.com",
            roles=[UserRole.USER],
            teams=[],
        )

    @pytest.mark.asyncio
    async def test_create_map_success(self, service, mock_repo, admin_user):
        """Test successful map creation by admin."""
        map_create = MapCreate(
            name="New Map", atlas_id=1, description="Desc", style="default"
        )

        # Mock Atlas Retrieval via repository helper
        atlas_mock = Mock(id=1, created_by_id=admin_user.id)
        mock_repo.get_related_entity.return_value = atlas_mock

        created_map = Mock(id=10)
        created_map.name = "New Map"
        mock_repo.create.return_value = created_map

        result = await service.create_map(map_create, admin_user)

        assert result.id == 10
        mock_repo.create.assert_awaited_once()
        mock_repo.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_map_permission_denied(self, service, mock_repo, user):
        """Test map creation denied if not owner or admin."""
        map_create = MapCreate(
            name="New Map", atlas_id=1, description="Desc", style="default"
        )

        # Atlas owned by someone else
        atlas_mock = Mock(id=1, created_by_id=99)
        mock_repo.get_related_entity.return_value = atlas_mock
        service._check_team_map_permission = AsyncMock(return_value=False)

        with pytest.raises(PermissionDeniedException) as exc:
            await service.create_map(map_create, user)

        assert exc.value.params["detail"] == "map.create_permission_denied"

    @pytest.mark.asyncio
    async def test_get_map_success(self, service, mock_repo, user):
        """Test get public map success."""
        map_obj = Mock(
            id=10,
            access_policy=AccessPolicy.PUBLIC,
            created_by_id=99,
            atlas_id=1,
            description="desc",
            style="default",
        )
        map_obj.name = "Public Map"
        mock_repo.get_or_raise.return_value = map_obj

        result = await service.get_map(10, user)
        assert result.id == 10

    @pytest.mark.asyncio
    async def test_get_map_not_found(self, service, mock_repo, user):
        """Test get map not found."""
        mock_repo.get_or_raise.side_effect = EntityNotFoundException(
            entity="Map", key="map.not_found", params={"id": 999}
        )

        with pytest.raises(EntityNotFoundException) as exc:
            await service.get_map(999, user)

        assert exc.value.key == "map.not_found"

    @pytest.mark.asyncio
    async def test_update_map_permission_denied(self, service, mock_repo, user):
        """Test update permission denied."""
        map_obj = Mock(id=10, created_by_id=99, atlas_id=1)
        mock_repo.get_or_raise.return_value = map_obj
        service._check_team_map_permission = AsyncMock(return_value=False)

        update = MapUpdate(name="Updated")

        with pytest.raises(PermissionDeniedException) as exc:
            await service.update_map(10, update, user)

        assert exc.value.params["detail"] == "map.update_permission_denied"

    @pytest.mark.asyncio
    async def test_delete_map_success(self, service, mock_repo, admin_user):
        """Test delete map success."""
        map_obj = Mock(id=10, created_by_id=1, atlas_id=1)
        mock_repo.get_or_raise.return_value = map_obj
        mock_repo.delete.return_value = True

        result = await service.delete_map(10, admin_user)
        assert result is True
        mock_repo.delete.assert_called_once_with(10)
