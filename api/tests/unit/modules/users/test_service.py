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
        repo = AsyncMock()
        repo.session = AsyncMock()
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

    # =========================================================================
    # Create User Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_user_success(self, service, mock_repo):
        """Test successful user creation."""
        from app.modules.users.schemas import UserCreate

        user_create = UserCreate(
            username="newuser", email="new@test.com", password="password12345"
        )
        created_user = Mock(
            id=1,
            username="newuser",
            email="new@test.com",
            roles=[UserRole.USER],
            teams=[],
            is_verified=False,
        )
        # Mock all methods called by create_user
        mock_repo.validate_unique_credentials = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock(return_value=created_user)
        mock_repo.get = AsyncMock(return_value=created_user)

        result = await service.create_user(user_create, is_verified=False)

        assert result.username == "newuser"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, service, mock_repo):
        """Test user creation with duplicate email raises exception."""
        from app.core.exceptions import DuplicateEntityException
        from app.modules.users.schemas import UserCreate

        user_create = UserCreate(
            username="newuser", email="existing@test.com", password="password12345"
        )
        # Raise duplicate exception from validation step
        mock_repo.validate_unique_credentials = AsyncMock(
            side_effect=DuplicateEntityException(
                key="user.email_exists", params={"email": "existing@test.com"}
            )
        )

        with pytest.raises(DuplicateEntityException) as exc:
            await service.create_user(user_create, is_verified=False)

        assert exc.value.key == "user.email_exists"

    # =========================================================================
    # Get User Internal Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_user_internal_success(self, service, mock_repo):
        """Test get_user_internal returns user without permission check."""
        user = Mock(
            id=1,
            username="internal",
            email="internal@test.com",
            roles=[UserRole.USER],
            teams=[],
            is_verified=True,
        )
        mock_repo.get_or_raise = AsyncMock(return_value=user)

        result = await service.get_user_internal(1)

        assert result.id == 1
        mock_repo.get_or_raise.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_internal_not_found(self, service, mock_repo):
        """Test get_user_internal raises exception for missing user."""
        mock_repo.get_or_raise = AsyncMock(
            side_effect=EntityNotFoundException(
                entity="User", key="user.not_found", params={"id": 999}
            )
        )

        with pytest.raises(EntityNotFoundException) as exc:
            await service.get_user_internal(999)

        assert exc.value.key == "user.not_found"

    # =========================================================================
    # Verify User Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_verify_user_success(self, service, mock_repo):
        """Test successful user verification."""
        user = Mock(is_verified=False, verification_token="valid_token")
        mock_repo.get_by_verification_token = AsyncMock(return_value=user)
        mock_repo.session.commit = AsyncMock()

        result = await service.verify_user("valid_token")

        assert result is True
        assert user.is_verified is True
        assert user.verification_token is None

    @pytest.mark.asyncio
    async def test_verify_user_invalid_token(self, service, mock_repo):
        """Test verification with invalid token returns False."""
        mock_repo.get_by_verification_token = AsyncMock(return_value=None)

        result = await service.verify_user("invalid_token")

        assert result is False

    # =========================================================================
    # Authenticate User Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, service, mock_repo):
        """Test successful authentication."""
        from app.core.hashing import hash_password

        hashed = hash_password("correctpassword")
        user = Mock(
            id=1,
            username="authuser",
            email="auth@test.com",
            hashed_password=hashed,
            roles=[UserRole.USER],
        )
        mock_repo.get_by_username = AsyncMock(return_value=user)

        result = await service.authenticate_user("authuser", "correctpassword")

        assert result.username == "authuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, service, mock_repo):
        """Test authentication with wrong password raises exception."""
        from app.core.exceptions import AuthenticationException
        from app.core.hashing import hash_password

        hashed = hash_password("correctpassword")
        user = Mock(hashed_password=hashed)
        mock_repo.get_by_username = AsyncMock(return_value=user)

        with pytest.raises(AuthenticationException) as exc:
            await service.authenticate_user("authuser", "wrongpassword")

        assert exc.value.key == "auth.failed"

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, service, mock_repo):
        """Test authentication for non-existent user raises exception."""
        from app.core.exceptions import AuthenticationException

        mock_repo.get_by_username = AsyncMock(return_value=None)

        with pytest.raises(AuthenticationException) as exc:
            await service.authenticate_user("ghost", "anypassword")

        assert exc.value.key == "auth.failed"

    # =========================================================================
    # Get or Create Google User Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_or_create_google_user_existing(self, service, mock_repo):
        """Test get_or_create returns existing user."""
        existing_user = Mock(
            id=1,
            username="googleuser",
            email="google@test.com",
            roles=[UserRole.USER],
            teams=[],
            is_verified=True,
        )
        mock_repo.get_by_email = AsyncMock(return_value=existing_user)

        user_info = {"email": "google@test.com", "name": "Google User"}
        result = await service.get_or_create_google_user(user_info)

        assert result.id == 1
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_google_user_new(self, service, mock_repo):
        """Test get_or_create creates new user for Google OAuth."""
        mock_repo.get_by_email = AsyncMock(return_value=None)
        new_user = Mock(
            id=2,
            username="newgoogleuser",
            email="newgoogle@test.com",
            roles=[UserRole.USER],
            teams=[],
            is_verified=True,
        )
        # Mock all methods called by create_user
        mock_repo.validate_unique_credentials = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock(return_value=new_user)
        mock_repo.get = AsyncMock(return_value=new_user)

        user_info = {"email": "newgoogle@test.com", "name": "New Google User"}
        result = await service.get_or_create_google_user(user_info)

        assert result.id == 2
        mock_repo.create.assert_called_once()
