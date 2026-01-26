import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validation_error_format(client: AsyncClient):
    """
    Test that Pydantic validation errors are formatted correctly
    according to our new standardized JSON structure.
    """
    # Sending invalid data (missing required fields) to login endpoint
    response = await client.post("/auth/login", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()

    # Check top-level structure
    assert "detail" in data
    assert "key" in data
    assert "params" in data

    assert data["key"] == "VALIDATION_ERROR"
    assert "errors" in data["params"]
    assert isinstance(data["params"]["errors"], list)


@pytest.mark.asyncio
async def test_auth_error_headers(client: AsyncClient):
    """
    Test that authentication errors include the WWW-Authenticate header.
    """
    # Access a protected endpoint without token
    response = await client.get("/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Bearer"
