from unittest.mock import patch

import pytest
from app.modules.users.schemas import UserDetail
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, user_data):
    """Test user registration via /auth/register."""
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_out = UserDetail(**data)
    assert user_out.email == user_data["email"]
    assert user_out.teams == []
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient, user_data):
    """Test user registration with existing data should fail."""
    # Register once
    await client.post("/auth/register", json=user_data)

    # Register again with same data
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 409
    data = response.json()
    assert data["key"] == "user.email_exists"


@pytest.mark.asyncio
async def test_google_login(client: AsyncClient):
    """Test Google Login redirect."""
    with patch(
        "app.modules.auth.services.auth_service.GoogleAuthService.login"
    ) as mock_login:
        # Mock the return value of GoogleAuthService.login
        # It usually returns a Starlette RedirectResponse or similar,
        # but the endpoint returns whatever the service returns.
        # Let's assume the service returns a dict or response.
        # Based on code: return await oauth.google.authorize_redirect(request, redirect_uri)
        # Verify checking the endpoint code: return await service.google_login(request)

        mock_login.return_value = {
            "url": "https://accounts.google.com/o/oauth2/auth..."
        }

        response = await client.get("/auth/google")
        assert response.status_code == 200
        assert mock_login.called


@pytest.mark.asyncio
async def test_google_callback(client: AsyncClient):
    """Test Google Callback creating a user."""
    mock_user_info = {
        "email": "googleuser@example.com",
        "name": "Google User",
        "picture": "http://example.com/avatar.jpg",
    }

    with patch(
        "app.modules.auth.services.auth_service.GoogleAuthService.callback"
    ) as mock_callback:
        mock_callback.return_value = mock_user_info

        # simulate callback request
        response = await client.get("/auth/google/callback")

        assert response.status_code == 200
        data = response.json()

        # Verify token is returned
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify user persistence
        token = data["access_token"]
        me_resp = await client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        me = me_resp.json()
        assert me["email"] == "googleuser@example.com"
        assert me["username"] == "Google User"


@pytest.mark.asyncio
async def test_login(client: AsyncClient, auth_token_factory, existing_users, settings):
    """Test login via /auth/login."""
    token = await auth_token_factory(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    assert token is not None
    assert len(token) > 0

    # Verify token content
    from app.core.security import decode_token

    payload = decode_token(token, settings)

    assert payload["username"] == existing_users[0]["username"]
    assert payload["email"] == existing_users[0]["email"]
    assert isinstance(payload["id"], int)
    assert "roles" in payload
