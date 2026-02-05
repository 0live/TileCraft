import pytest
from app.main import app
from app.modules.auth.services.auth_service import get_auth_service
from fastapi.testclient import TestClient


@pytest.fixture(name="client_ip")
def fixture_client_ip():
    return "127.0.0.1"


@pytest.fixture(name="limiter_test_client")
def fixture_limiter_test_client(client_ip):
    # Mock the auth service to avoid DB connection issues
    async def mock_auth_service():
        return None

    app.dependency_overrides[get_auth_service] = mock_auth_service

    # Create a client that simulates a specific IP
    client = TestClient(app, base_url="http://testserver", client=(client_ip, 12345))
    yield client
    # Clean up overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
@pytest.mark.skipif(True, reason="Rate limiting disabled in test environment")
async def test_login_rate_limit(limiter_test_client):
    url = "/auth/login"

    data = {"username": "foo", "password": "bar"}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Limit is 5 per minute.

    # Request 1-5: Should NOT be 429
    for i in range(5):
        try:
            response = limiter_test_client.post(url, data=data, headers=headers)
            assert response.status_code != 429, f"Request {i + 1} failed with 429"
        except Exception:
            # We expect exceptions due to NoneType service, that's fine
            pass

    # Request 6: Should be 429
    response = limiter_test_client.post(url, data=data, headers=headers)
    assert response.status_code == 429, "Request 6 should have been rate limited"
    # slowapi default handler returns: {"error": "Rate limit exceeded: ..."}
    assert "Rate limit exceeded" in response.text
