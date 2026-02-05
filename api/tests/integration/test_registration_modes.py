from unittest.mock import patch

import pytest
from httpx import AsyncClient

# We don't need get_settings here if we use the fixture
# from app.core.config import get_settings


@pytest.mark.asyncio
async def test_registration_disabled(client: AsyncClient, user_data, settings):
    """Test public registration when disabled."""
    # Patch the settings object that is injected into the app via dependency_overrides
    with patch.object(settings, "allow_self_registration", False):
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 403
        assert response.json()["detail"] == "Self-registration is disabled."


@pytest.mark.asyncio
async def test_registration_allowed(client: AsyncClient, user_data, settings):
    """Test public registration when allowed."""
    with patch.object(settings, "allow_self_registration", True):
        # Using a new email to avoid conflict
        user_data["email"] = "allowed@example.com"
        user_data["username"] = "allowed_user"

        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        assert response.json()["email"] == "allowed@example.com"


@pytest.mark.asyncio
async def test_admin_create_user(
    client: AsyncClient, auth_token_factory, existing_users, user_data
):
    """Test admin creating a user."""
    # Log in as admin
    admin_user = existing_users[2]  # admin@test.com
    token = await auth_token_factory(
        username=admin_user["username"], password=admin_user["password"]
    )

    user_data["email"] = "admin_created@example.com"
    user_data["username"] = "admin_created"

    response = await client.post(
        "/users", json=user_data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin_created@example.com"
    assert data["is_verified"] is True


@pytest.mark.asyncio
async def test_admin_create_user_as_user(
    client: AsyncClient, auth_token_factory, existing_users, user_data
):
    """Test regular user cannot create users via admin endpoint."""
    # Log in as user
    regular_user = existing_users[0]  # user@test.com
    token = await auth_token_factory(
        username=regular_user["username"], password=regular_user["password"]
    )

    response = await client.post(
        "/users", json=user_data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_smtp_configuration_resilience(
    client: AsyncClient, auth_token_factory, existing_users, user_data, settings
):
    """
    Test that application (Admin User Create) works even if SMTP config is missing/invalid
    when self-registration is disabled.
    """
    admin_user = existing_users[2]
    token = await auth_token_factory(
        username=admin_user["username"], password=admin_user["password"]
    )

    user_data["email"] = "resilient@example.com"
    user_data["username"] = "resilient"

    with patch.object(settings, "allow_self_registration", False):
        # Mock SMTP settings to be broken/missing
        with patch.object(settings, "smtp_host", None):
            # Admin creation should bypass email verification sending entirely
            response = await client.post(
                "/users", json=user_data, headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            assert response.json()["is_verified"] is True


@pytest.mark.asyncio
async def test_google_auth_restricted_when_registration_disabled(
    client: AsyncClient, settings
):
    """
    Test that Google Auth endpoints return 403 when registration is disabled.
    """
    with (
        patch.object(settings, "allow_self_registration", False),
        patch.object(settings, "activate_google_auth", True),
    ):
        # Test Login init
        response = await client.get("/auth/google")
        assert response.status_code == 403
        assert response.json()["detail"] == "Self-registration is disabled."

        # Test Callback
        response = await client.get("/auth/google/callback?code=fake_code")
        assert response.status_code == 403
        assert response.json()["detail"] == "Self-registration is disabled."
