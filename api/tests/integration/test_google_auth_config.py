from unittest.mock import patch

import pytest
from app.core.config import get_settings
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_google_login_disabled(client: AsyncClient):
    """Test Google Login endpoint when feature is disabled."""
    settings = get_settings()
    # We need to patch the settings on the service instance or globally
    # Since get_settings is lru_cached, we can try to patch the value on the instance returned

    with patch.object(settings, "activate_google_auth", False):
        response = await client.get("/auth/google")
        # Currently it returns 500 because of the missing oauth config check in GoogleAuthService
        # We want it to be 404 per the plan (or checking the service logic)
        # For reproduction, we assert what we expect to FAIL or what currently happens
        # The user said "not disabling the endpoints", so we expect 200 or 500, but we WANT 404.

        # If the fix works, this should be 404.
        # Before the fix, it enters the service and hits "Google OAuth configuration failed" (500)
        # or just tries to redirect if oauth keys are somehow present but flag is false (unlikely config combo but possible)

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Google authentication is disabled."


@pytest.mark.asyncio
async def test_google_callback_disabled(client: AsyncClient):
    """Test Google Callback endpoint when feature is disabled."""
    settings = get_settings()
    with patch.object(settings, "activate_google_auth", False):
        response = await client.get("/auth/google/callback")
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Google authentication is disabled."
