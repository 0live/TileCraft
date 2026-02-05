from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.exceptions import AuthenticationException
from app.modules.auth.services.auth_service import AuthService
from app.modules.users.schemas import UserCreate, UserDetail


class TestAuthService:
    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_user_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_settings(self):
        return Settings(
            private_key="test_secret_key",
            refresh_token_expire_days=30,
            access_token_expire_minutes=15,
            allow_self_registration=True,
        )

    @pytest.fixture
    def mock_email_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_google_auth_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_repo,
        mock_user_service,
        mock_email_service,
        mock_google_auth_service,
        mock_settings,
    ):
        return AuthService(
            repository=mock_repo,
            user_service=mock_user_service,
            email_service=mock_email_service,
            google_auth_service=mock_google_auth_service,
            settings=mock_settings,
        )

    @pytest.fixture
    def mock_response(self):
        response = Mock()
        response.set_cookie = Mock()
        response.delete_cookie = Mock()
        return response

    @pytest.fixture
    def sample_user(self):
        return UserDetail(
            id=1,
            username="testuser",
            email="test@example.com",
            roles=[],
            teams=[],
            is_verified=True,
        )

    # =========================================================================
    # Register Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_register_success(
        self, service, mock_user_service, mock_email_service
    ):
        """Test successful user registration."""
        user_create = UserCreate(
            username="newuser", email="new@test.com", password="password12345"
        )
        expected_user = UserDetail(
            id=1,
            username="newuser",
            email="new@test.com",
            roles=[],
            teams=[],
            is_verified=False,
        )
        mock_user_service.create_user = AsyncMock(return_value=expected_user)

        result = await service.register(user_create)

        assert result.username == "newuser"
        assert result.is_verified is False
        mock_user_service.create_user.assert_called_once()
        mock_email_service.send_verification_email.assert_called_once()

    # =========================================================================
    # Login Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_login_success(
        self, service, mock_repo, mock_user_service, mock_response, sample_user
    ):
        """Test successful login returns tokens."""
        mock_user_service.authenticate_user = AsyncMock(return_value=sample_user)
        mock_repo.create_refresh_token = AsyncMock()

        result = await service.login("testuser", "password", mock_response)

        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.refresh_token is not None
        mock_response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, service, mock_user_service, mock_response
    ):
        """Test login with invalid credentials raises exception."""
        mock_user_service.authenticate_user = AsyncMock(
            side_effect=AuthenticationException(params={"detail": "auth.failed"})
        )

        with pytest.raises(AuthenticationException) as exc:
            await service.login("testuser", "wrongpassword", mock_response)

        assert exc.value.params["detail"] == "auth.failed"

    # =========================================================================
    # Refresh Token Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, service, mock_repo, mock_user_service, mock_response, sample_user
    ):
        """Test successful token refresh."""
        stored_token = Mock(
            id=1,
            user_id=1,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        mock_repo.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)
        mock_repo.revoke_refresh_token = AsyncMock()
        mock_repo.create_refresh_token = AsyncMock()
        mock_user_service.get_user_internal = AsyncMock(return_value=sample_user)

        result = await service.refresh_access_token("valid_token", mock_response)

        assert result.access_token is not None
        mock_repo.revoke_refresh_token.assert_called_once_with(stored_token.id)
        mock_response.set_cookie.assert_called()

    @pytest.mark.asyncio
    async def test_refresh_token_missing(self, service, mock_response):
        """Test refresh with missing token raises exception."""
        with pytest.raises(AuthenticationException) as exc:
            await service.refresh_access_token(None, mock_response)

        assert exc.value.params["detail"] == "auth.refresh_token_missing"
        mock_response.delete_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, service, mock_repo, mock_response):
        """Test refresh with expired token raises exception."""
        stored_token = Mock(
            id=1,
            user_id=1,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        mock_repo.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)
        mock_repo.revoke_refresh_token = AsyncMock()

        with pytest.raises(AuthenticationException) as exc:
            await service.refresh_access_token("expired_token", mock_response)

        assert exc.value.params["detail"] == "auth.refresh_token_invalid"
        mock_repo.revoke_refresh_token.assert_called_once()
        mock_response.delete_cookie.assert_called()

    # =========================================================================
    # Logout Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_logout_success(self, service, mock_repo, mock_response):
        """Test successful logout revokes token."""
        stored_token = Mock(id=1)
        mock_repo.get_refresh_token_by_hash = AsyncMock(return_value=stored_token)
        mock_repo.revoke_refresh_token = AsyncMock()

        await service.logout("valid_token", mock_response)

        mock_repo.revoke_refresh_token.assert_called_once_with(1)
        mock_response.delete_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_no_token(self, service, mock_repo, mock_response):
        """Test logout without token still clears cookie."""
        await service.logout(None, mock_response)

        mock_repo.get_refresh_token_by_hash.assert_not_called()
        mock_response.delete_cookie.assert_called_once()

    # =========================================================================
    # Email Verification Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_verify_email_success(self, service, mock_user_service):
        """Test successful email verification."""
        mock_user_service.verify_user = AsyncMock(return_value=True)

        await service.verify_email("valid_token")

        mock_user_service.verify_user.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_verify_email_invalid(self, service, mock_user_service):
        """Test invalid verification token raises exception."""
        mock_user_service.verify_user = AsyncMock(return_value=False)

        with pytest.raises(AuthenticationException) as exc:
            await service.verify_email("invalid_token")

        assert exc.value.params["detail"] == "auth.verification_failed"
