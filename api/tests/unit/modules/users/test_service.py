from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserCreate, UserDetail, UserUpdate
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
    async def test_create_user_success(self, service, mock_repo):
        """Test successful user creation."""
        # Setup
        user_create = UserCreate(
            username="newuser", email="new@example.com", password="password123"
        )
        mock_repo.get_by_email = AsyncMock(return_value=None)
        mock_repo.get_by_username = AsyncMock(return_value=None)

        created_user = Mock(id=1)
        mock_repo.create = AsyncMock(return_value=created_user)

        expected_detail = UserDetail(
            id=1,
            username="newuser",
            email="new@example.com",
            roles=[UserRole.USER],
            teams=[],
        )
        mock_repo.get = AsyncMock(return_value=expected_detail)

        # Execute
        result = await service.create_user(user_create)

        # Assert
        assert result.username == "newuser"
        assert result.email == "new@example.com"
        mock_repo.create.assert_called_once()
        mock_repo.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, service, mock_repo):
        """Test user creation with existing email."""
        user_create = UserCreate(
            username="newuser", email="existing@example.com", password="password123"
        )
        mock_repo.get_by_email = AsyncMock(return_value=Mock())

        with pytest.raises(DuplicateEntityException) as exc:
            await service.create_user(user_create)

        assert exc.value.key == "user.email_exists"
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, service, mock_repo):
        """Test user creation with existing username."""
        user_create = UserCreate(
            username="existinguser", email="new@example.com", password="password123"
        )
        mock_repo.get_by_email = AsyncMock(return_value=None)
        mock_repo.get_by_username = AsyncMock(return_value=Mock())

        with pytest.raises(DuplicateEntityException) as exc:
            await service.create_user(user_create)

        assert exc.value.key == "user.username_exists"
        mock_repo.create.assert_not_called()

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

        mock_repo.get = AsyncMock(return_value=target_user)

        result = await service.get_user_by_id(1, admin_user)
        assert result.id == 1
        assert result.username == "target"

    @pytest.mark.asyncio
    async def test_get_user_by_id_success_self(self, service, mock_repo):
        """Test get user by id as self."""
        user = UserDetail(
            id=1, username="me", email="me@test.com", roles=[UserRole.USER], teams=[]
        )

        mock_repo.get = AsyncMock(return_value=user)

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
        mock_repo.get = AsyncMock(return_value=None)

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
