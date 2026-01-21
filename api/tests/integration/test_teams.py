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


@pytest.mark.asyncio
async def test_get_team_by_id(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a team
    create_res = await client.post(
        "/teams",
        json={"name": "Team For Get"},
        headers=headers,
    )
    team_id = create_res.json()["id"]

    # Get the team
    response = await client.get(f"/teams/{team_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Team For Get"
    assert data["id"] == team_id


@pytest.mark.asyncio
async def test_update_team(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a team
    create_res = await client.post(
        "/teams",
        json={"name": "Team For Update"},
        headers=headers,
    )
    team_id = create_res.json()["id"]

    # Update the team
    response = await client.patch(
        f"/teams/{team_id}",
        json={"name": "Updated Team Name"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Team Name"
    assert data["id"] == team_id

    # Verify update with GET
    get_res = await client.get(f"/teams/{team_id}", headers=headers)
    assert get_res.json()["name"] == "Updated Team Name"


@pytest.mark.asyncio
async def test_delete_team(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a team
    create_res = await client.post(
        "/teams",
        json={"name": "Team For Delete"},
        headers=headers,
    )
    team_id = create_res.json()["id"]

    # Delete the team
    response = await client.delete(f"/teams/{team_id}", headers=headers)
    assert response.status_code == 200

    # Verify deletion with GET
    get_res = await client.get(f"/teams/{team_id}", headers=headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_team(client: AsyncClient, auth_token_factory):
    """
    Verify that creating a team with a duplicate name returns 409 Conflict.
    """
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create first team
    response = await client.post(
        "/teams",
        json={"name": "Unique Team"},
        headers=headers,
    )
    assert response.status_code == 200

    # 2. Try to create second team with same name
    response = await client.post(
        "/teams",
        json={"name": "Unique Team"},
        headers=headers,
    )
    assert response.status_code == 409
    data = response.json()
    assert data["key"] == "team.name_exists"
