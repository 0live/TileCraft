import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_map(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create an atlas first (required for map creation)
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas for Map", "description": "Atlas Desc"},
        headers=headers,
    )
    assert resp.status_code == 200
    atlas_id = resp.json()["id"]

    response = await client.post(
        "/maps",
        json={
            "name": "New Map",
            "style": "dark",
            "description": "Test Map",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Map"
    assert data["style"] == "dark"
    assert "id" in data
    assert data["atlas_id"] == atlas_id


@pytest.mark.asyncio
async def test_get_map(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas for Map", "description": "Atlas Desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create Map
    response = await client.post(
        "/maps",
        json={
            "name": "New Map",
            "style": "dark",
            "description": "Test Map",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )
    assert response.status_code == 200
    map_id = response.json()["id"]

    # Get Map
    response = await client.get(f"/maps/{map_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == map_id
    assert data["name"] == "New Map"
    assert data["atlas_id"] == atlas_id


@pytest.mark.asyncio
async def test_get_all_maps(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create an atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas for All Maps", "description": "Atlas Desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create a map
    await client.post(
        "/maps",
        json={
            "name": "Another Map",
            "style": "light",
            "description": "Test Map",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )

    response = await client.get("/maps", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(t["name"] == "Another Map" for t in data)


@pytest.mark.asyncio
async def test_update_map(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas for Update Map", "description": "Atlas Desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create Map
    response = await client.post(
        "/maps",
        json={
            "name": "Map To Update",
            "style": "style",
            "description": "Desc",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )
    map_id = response.json()["id"]

    # Update Map
    response = await client.patch(
        f"/maps/{map_id}",
        json={"name": "Updated Map Name", "description": "Updated Desc"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Map Name"
    assert data["description"] == "Updated Desc"
    assert data["id"] == map_id

    # Verify update with GET
    get_res = await client.get(f"/maps/{map_id}", headers=headers)
    assert get_res.json()["name"] == "Updated Map Name"


@pytest.mark.asyncio
async def test_get_delete_map(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas for Delete", "description": "Atlas Desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create Map
    response = await client.post(
        "/maps",
        json={
            "name": "Map To Delete",
            "style": "style",
            "description": "Desc",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )
    assert response.status_code == 200
    map_id = response.json()["id"]

    # Get Map
    response = await client.get(f"/maps/{map_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == map_id
    assert data["name"] == "Map To Delete"
    assert data["atlas_id"] == atlas_id

    # Delete Map
    response = await client.delete(f"/maps/{map_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() is True

    # Get Map again (should be 404)
    response = await client.get(f"/maps/{map_id}", headers=headers)
    assert response.status_code == 404
