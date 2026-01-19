import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_map(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/maps",
        json={"name": "New Map", "style": "dark", "description": "Test Map"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Map"
    assert data["style"] == "dark"
    assert "id" in data
    assert isinstance(data["atlases"], list)


@pytest.mark.asyncio
async def test_get_all_maps(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a map first
    await client.post(
        "/maps",
        json={"name": "Another Map", "style": "light", "description": "Test Map"},
        headers=headers,
    )

    response = await client.get("/maps", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(t["name"] == "Another Map" for t in data)
