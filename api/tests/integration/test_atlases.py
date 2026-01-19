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


@pytest.mark.asyncio
async def test_delete_atlas(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create an atlas to delete
    response = await client.post(
        "/atlases",
        json={"name": "Atlas To Delete", "description": "Will be deleted"},
        headers=headers,
    )
    assert response.status_code == 200
    atlas_id = response.json()["id"]

    # Delete it
    response = await client.delete(f"/atlases/{atlas_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() is True

    # Verify it's gone from list (or 404 on get by id if endpoint existed, but we only have get_all)
    response = await client.get("/atlases", headers=headers)
    data = response.json()
    assert not any(a["id"] == atlas_id for a in data)


@pytest.mark.asyncio
async def test_update_atlas_maps(client: AsyncClient, auth_token_factory):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create maps
    map_ids = []
    for i in range(2):
        resp = await client.post(
            "/maps",
            json={"name": f"Map {i}", "description": "desc", "style": "{}."},
            headers=headers,
        )
        assert resp.status_code == 200
        map_ids.append(resp.json()["id"])

    # Create atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas Maps Test", "description": "desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Add Map 0
    resp = await client.patch(
        f"/atlases/{atlas_id}",
        json={"maps": [map_ids[0]]},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["maps"]) == 1
    assert data["maps"][0]["id"] == map_ids[0]

    # Add Map 1 (should append if logic was append, but our new logic is toggle?
    # Wait, the logic I implemented was:
    # for map_id in maps: if present remove, else add.
    # So if I send [map_ids[1]], map 0 remains?
    # NO. The implementation iterates over the input list.
    # It does NOT touch maps NOT in the input list.
    # So sending [map_ids[1]] will add map 1. Map 0 is untouched.
    resp = await client.patch(
        f"/atlases/{atlas_id}",
        json={"maps": [map_ids[1]]},
        headers=headers,
    )
    data = resp.json()
    assert len(data["maps"]) == 2

    # Remove Map 0 (send it again to toggle off)
    resp = await client.patch(
        f"/atlases/{atlas_id}",
        json={"maps": [map_ids[0]]},
        headers=headers,
    )
    data = resp.json()
    assert len(data["maps"]) == 1
    assert data["maps"][0]["id"] == map_ids[1]


@pytest.mark.asyncio
async def test_manage_atlas_team_link_lifecycle(
    client: AsyncClient, auth_token_factory
):
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create team
    resp = await client.post(
        "/teams",
        json={"name": "Link Test Team"},
        headers=headers,
    )
    team_id = resp.json()["id"]

    # Create atlas
    resp = await client.post(
        "/atlases",
        json={"name": "Atlas Link Test", "description": "desc"},
        headers=headers,
    )
    atlas_id = resp.json()["id"]

    # Create Link
    link_payload = {
        "atlas_id": atlas_id,
        "team_id": team_id,
        "can_manage_atlas": False,
        "can_create_maps": True,
        "can_edit_maps": False,
    }
    resp = await client.post("/atlases/team", json=link_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_create_maps"] is True
    assert data["can_manage_atlas"] is False

    # Update Link
    link_payload["can_manage_atlas"] = True
    resp = await client.post("/atlases/team", json=link_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_manage_atlas"] is True

    # Delete Link
    resp = await client.delete(f"/atlases/{atlas_id}/team/{team_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json() is True
