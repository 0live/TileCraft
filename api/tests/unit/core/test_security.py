from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.exceptions import AuthenticationException
from app.core.hashing import hash_password, verify_password
from app.core.security import (
    create_access_token,
    decode_token,
    get_current_user,
    get_token,
)
from app.modules.users.schemas import UserDetail


class TestSecurity:
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "secure_password"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_token_creation_and_decoding(self):
        """Test JWT token creation and decoding."""
        settings = Settings(
            access_token_expire_minutes=15, algorithm="HS256", private_key="secret"
        )
        data = {"sub": "test_user", "username": "test_user"}

        token = create_access_token(data, settings)
        decoded = decode_token(token, settings)

        assert decoded["sub"] == "test_user"
        assert decoded["username"] == "test_user"
        assert "exp" in decoded

    def test_get_token(self):
        """Test get_token wrapper."""
        settings = Settings(
            access_token_expire_minutes=15, algorithm="HS256", private_key="secret"
        )
        user = UserDetail(id=1, username="test", email="test@example.com", roles=[])

        token_response = get_token(user, settings)
        assert token_response.token_type == "bearer"
        assert token_response.access_token

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test get_current_user success path."""
        settings = Settings(
            access_token_expire_minutes=15, algorithm="HS256", private_key="secret"
        )
        token = create_access_token({"username": "test_user"}, settings)

        service_mock = Mock()
        service_mock.settings = settings
        service_mock.get_by_username = AsyncMock(
            return_value=Mock(
                id=1,
                username="test_user",
                email="test@example.com",
                hashed_password="hash",
                roles=[],
                teams=[],
                is_verified=True,
            )
        )

        user = await get_current_user(token, service_mock)
        assert user.username == "test_user"
        service_mock.get_by_username.assert_called_once_with(
            "test_user", with_relations=True
        )

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        settings = Settings(
            access_token_expire_minutes=15, algorithm="HS256", private_key="secret"
        )
        service_mock = Mock()
        service_mock.settings = settings

        with pytest.raises(AuthenticationException) as exc:
            await get_current_user("invalid_token", service_mock)
        assert exc.value.key == "auth.failed"
        assert exc.value.params["detail"] == "auth.invalid_credentials"

    @pytest.mark.asyncio
    async def test_get_current_user_no_username(self):
        """Test get_current_user with token missing username."""
        settings = Settings(
            access_token_expire_minutes=15, algorithm="HS256", private_key="secret"
        )
        token = create_access_token({"sub": "no_username"}, settings)

        service_mock = Mock()
        service_mock.settings = settings

        with pytest.raises(AuthenticationException) as exc:
            await get_current_user(token, service_mock)
        assert exc.value.key == "auth.failed"
        assert exc.value.params["detail"] == "auth.invalid_credentials"

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test get_current_user where user does not exist."""
        settings = Settings(
            access_token_expire_minutes=15, algorithm="HS256", private_key="secret"
        )
        token = create_access_token({"username": "ghost"}, settings)

        service_mock = Mock()
        service_mock.settings = settings
        service_mock.get_by_username = AsyncMock(return_value=None)

        with pytest.raises(AuthenticationException) as exc:
            await get_current_user(token, service_mock)
        assert exc.value.key == "auth.failed"
        assert exc.value.params["detail"] == "auth.user_not_found"
