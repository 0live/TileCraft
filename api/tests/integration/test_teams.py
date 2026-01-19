import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_team(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/teams",
        json={"name": "New Team"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Team"
    assert "id" in data
    assert isinstance(data["users"], list)


@pytest.mark.asyncio
async def test_get_all_teams(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a team first
    await client.post(
        "/teams",
        json={"name": "Another Team"},
        headers=headers,
    )

    response = await client.get("/teams", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(t["name"] == "Another Team" for t in data)
