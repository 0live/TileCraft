from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.exceptions import (
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail, UserUpdate
from app.modules.users.service import UserService


class TestUserService:
    @pytest.fixture
    def mock_repo(self):
        repo = Mock()
        repo.session = AsyncMock()  # Mock session for commit
        return repo

    @pytest.fixture
    def mock_settings(self):
        return Settings()

    @pytest.fixture
    def service(self, mock_repo, mock_settings):
        return UserService(repository=mock_repo, settings=mock_settings)

    @pytest.mark.asyncio
    async def test_get_user_by_id_success_admin(self, service, mock_repo):
        """Test get user by id as admin."""
        admin_user = UserDetail(
            id=99,
            username="admin",
            email="admin@test.com",
            roles=[UserRole.ADMIN],
            teams=[],
        )
        target_user = UserDetail(
            id=1,
            username="target",
            email="target@test.com",
            roles=[UserRole.USER],
            teams=[],
        )

        mock_repo.get_or_raise = AsyncMock(return_value=target_user)

        result = await service.get_user_by_id(1, admin_user)
        assert result.id == 1
        assert result.username == "target"

    @pytest.mark.asyncio
    async def test_get_user_by_id_success_self(self, service, mock_repo):
        """Test get user by id as self."""
        user = UserDetail(
            id=1, username="me", email="me@test.com", roles=[UserRole.USER], teams=[]
        )

        mock_repo.get_or_raise = AsyncMock(return_value=user)

        result = await service.get_user_by_id(1, user)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_user_by_id_permission_denied(self, service, mock_repo):
        """Test get other user without admin role."""
        user = UserDetail(
            id=1, username="me", email="me@test.com", roles=[UserRole.USER], teams=[]
        )

        with pytest.raises(PermissionDeniedException) as exc:
            await service.get_user_by_id(2, user)

        assert exc.value.params["detail"] == "user.read_permission_denied"
        mock_repo.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, service, mock_repo):
        """Test get user by id not found."""
        admin_user = UserDetail(
            id=99,
            username="admin",
            email="admin@test.com",
            roles=[UserRole.ADMIN],
            teams=[],
        )
        from app.core.exceptions import EntityNotFoundException

        mock_repo.get_or_raise = AsyncMock(
            side_effect=EntityNotFoundException(
                entity="User", key="user.not_found", params={"id": 1}
            )
        )

        with pytest.raises(EntityNotFoundException) as exc:
            await service.get_user_by_id(1, admin_user)

        assert exc.value.key == "user.not_found"

    @pytest.mark.asyncio
    async def test_update_user_permission_denied(self, service):
        """Test update user without permission."""
        user = UserDetail(
            id=1, username="me", email="me@test.com", roles=[UserRole.USER], teams=[]
        )
        update_data = UserUpdate(username="newname")

        # Trying to update user 2
        with pytest.raises(PermissionDeniedException) as exc:
            await service.update_user(2, update_data, user)

        assert exc.value.params["detail"] == "user.update_permission_denied"

    @pytest.mark.asyncio
    async def test_update_user_role_denied(self, service):
        """Test updating roles without admin privileges."""
        user = UserDetail(
            id=1, username="me", email="me@test.com", roles=[UserRole.USER], teams=[]
        )
        update_data = UserUpdate(roles=[UserRole.ADMIN])

        with pytest.raises(PermissionDeniedException) as exc:
            await service.update_user(1, update_data, user)

        assert exc.value.params["detail"] == "user.role_permission_denied"

    @pytest.mark.asyncio
    async def test_delete_user_success(self, service, mock_repo):
        """Test successful user deletion by admin."""
        admin_user = UserDetail(
            id=99,
            username="admin",
            email="admin@test.com",
            roles=[UserRole.ADMIN],
            teams=[],
        )
        mock_repo.delete = AsyncMock(return_value=True)

        result = await service.delete_user(1, admin_user)

        assert "message" in result
        mock_repo.delete.assert_awaited_once_with(1)
        mock_repo.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, service, mock_repo):
        """Test deletion of non-existent user."""
        admin_user = UserDetail(
            id=99,
            username="admin",
            email="admin@test.com",
            roles=[UserRole.ADMIN],
            teams=[],
        )
        mock_repo.delete = AsyncMock(return_value=False)
        mock_repo.session.commit = AsyncMock()

        with pytest.raises(EntityNotFoundException) as exc:
            await service.delete_user(1, admin_user)

        assert exc.value.key == "user.not_found"
