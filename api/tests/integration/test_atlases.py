import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_atlas(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/atlases",
        json={"name": "New Atlas", "description": "Test Atlas Description"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Atlas"
    assert data["description"] == "Test Atlas Description"
    assert "id" in data
    assert isinstance(data["teams"], list)
    assert isinstance(data["maps"], list)


@pytest.mark.asyncio
async def test_get_all_atlases(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create an atlas first
    await client.post(
        "/atlases",
        json={"name": "Another Atlas", "description": "Another Description"},
        headers=headers,
    )

    response = await client.get("/atlases", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(a["name"] == "Another Atlas" for a in data)
