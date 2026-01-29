from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.enums.access_policy import AccessPolicy
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.atlases.schemas import AtlasBase, AtlasUpdate
from app.modules.atlases.service import AtlasService
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail


class TestAtlasService:
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
        return AtlasService(repository=mock_repo, settings=mock_settings)

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
    async def test_create_atlas_success(self, service, mock_repo, admin_user):
        """Test successful atlas creation by admin."""
        atlas_base = AtlasBase(
            name="New Atlas", access_policy=AccessPolicy.STANDARD, description="Desc"
        )
        mock_repo.get_by_name = AsyncMock(return_value=None)

        expected_detail = Mock(
            id=10,
            access_policy=AccessPolicy.STANDARD,
            description="Desc",
            created_by_id=admin_user.id,
            teams=[],
            maps=[],
        )
        expected_detail.name = "New Atlas"
        mock_repo.get = AsyncMock(return_value=expected_detail)

        result = await service.create_atlas(atlas_base, admin_user)

        assert result.name == "New Atlas"
        mock_repo.session.add.assert_called_once()
        mock_repo.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_atlas_permission_denied(self, service, mock_repo, user):
        """Test atlas creation denied for standard user."""
        atlas_base = AtlasBase(name="New Atlas", description="Desc")

        with pytest.raises(PermissionDeniedException) as exc:
            await service.create_atlas(atlas_base, user)

        assert exc.value.params["detail"] == "atlas.create_permission_denied"

    @pytest.mark.asyncio
    async def test_create_atlas_duplicate_name(self, service, mock_repo, admin_user):
        """Test atlas creation with duplicate name."""
        atlas_base = AtlasBase(name="Existing Atlas", description="Desc")
        mock_repo.ensure_unique_name.side_effect = DuplicateEntityException(
            key="atlas.name_exists", params={"name": "Existing Atlas"}
        )

        with pytest.raises(DuplicateEntityException) as exc:
            await service.create_atlas(atlas_base, admin_user)

        assert exc.value.key == "atlas.name_exists"
        mock_repo.session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_atlas_success(self, service, mock_repo, user):
        """Test get public atlas success."""
        atlas = Mock(
            id=10,
            access_policy=AccessPolicy.PUBLIC,
            description="Desc",
            created_by_id=99,
            teams=[],
            maps=[],
        )
        atlas.name = "Public Atlas"
        mock_repo.get_or_raise.return_value = atlas

        result = await service.get_atlas(10, user)
        assert result.id == 10

    @pytest.mark.asyncio
    async def test_get_atlas_private_denied(self, service, mock_repo, user):
        """Test get private atlas denied."""
        atlas = Mock(
            id=10,
            access_policy=AccessPolicy.STANDARD,
            description="Desc",
            created_by_id=99,
            teams=[],
            maps=[],
        )
        atlas.name = "Private Atlas"
        mock_repo.get_or_raise.return_value = atlas

        with pytest.raises(EntityNotFoundException) as exc:
            # Service raises EntityNotFound instead of PermissionDenied for security masking if desired logic
            # Checking implementation: logic says "if not can_view: raise EntityNotFoundException"
            await service.get_atlas(10, user)

        assert exc.value.key == "atlas.not_found"

    @pytest.mark.asyncio
    async def test_update_atlas_permission_denied(self, service, mock_repo, user):
        """Test update permission denied."""
        atlas = Mock(id=10, created_by_id=99)
        atlas.name = "Atlas"
        mock_repo.get_or_raise.return_value = atlas

        service._has_manage_permission = AsyncMock(return_value=False)

        update = AtlasUpdate(name="Updated")

        with pytest.raises(PermissionDeniedException) as exc:
            await service.update_atlas(10, update, user)

        assert exc.value.params["detail"] == "atlas.edit_permission_denied"

    @pytest.mark.asyncio
    async def test_delete_atlas_success(self, service, mock_repo, admin_user):
        """Test delete atlas success."""
        atlas = Mock(id=10, created_by_id=1)
        mock_repo.get_or_raise.return_value = atlas
        service._has_manage_permission = AsyncMock(return_value=True)
        mock_repo.delete.return_value = True

        result = await service.delete_atlas(10, admin_user)
        assert result is True
        mock_repo.delete.assert_called_once_with(10)
