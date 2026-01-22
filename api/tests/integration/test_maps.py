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


@pytest.mark.asyncio
async def test_create_duplicate_map_in_same_atlas(
    client: AsyncClient, auth_token_factory
):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas Unique", "description": "Atlas Desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create Map 1
    await client.post(
        "/maps",
        json={
            "name": "Map 1",
            "style": "dark",
            "description": "Test Map",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )

    # Create Duplicate Map
    response = await client.post(
        "/maps",
        json={
            "name": "Map 1",
            "style": "light",
            "description": "Duplicate Name",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_same_map_name_different_atlas(
    client: AsyncClient, auth_token_factory
):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Atlas 1
    resp1 = await client.post(
        "/atlases",
        json={"name": "Atlas 1 Unique", "description": "Atlas Desc"},
        headers=headers,
    )
    assert resp1.status_code == 200
    atlas_id_1 = resp1.json()["id"]

    # Create Atlas 2
    resp2 = await client.post(
        "/atlases",
        json={"name": "Atlas 2 Unique", "description": "Atlas Desc"},
        headers=headers,
    )
    assert resp2.status_code == 200
    atlas_id_2 = resp2.json()["id"]

    # Create Map in Atlas 1
    resp = await client.post(
        "/maps",
        json={
            "name": "Shared Name",
            "style": "dark",
            "description": "Test Map",
            "atlas_id": atlas_id_1,
        },
        headers=headers,
    )
    assert resp.status_code == 200

    # Create Map with same name in Atlas 2
    response = await client.post(
        "/maps",
        json={
            "name": "Shared Name",
            "style": "light",
            "description": "Same Name Diff Atlas",
            "atlas_id": atlas_id_2,
        },
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_map_to_duplicate_name(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas Update", "description": "Atlas Desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create Map A
    await client.post(
        "/maps",
        json={
            "name": "Map A",
            "style": "dark",
            "description": "Test Map",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )

    # Create Map B
    resp_b = await client.post(
        "/maps",
        json={
            "name": "Map B",
            "style": "light",
            "description": "Test Map",
            "atlas_id": atlas_id,
        },
        headers=headers,
    )
    map_id_b = resp_b.json()["id"]

    # Update Map B to name "Map A"
    response = await client.patch(
        f"/maps/{map_id_b}",
        json={"name": "Map A"},
        headers=headers,
    )
    assert response.status_code == 409
