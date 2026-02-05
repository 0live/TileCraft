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


@pytest.mark.asyncio
async def test_team_membership_management(
    client: AsyncClient, auth_token_factory, register_and_verify_user
):
    """
    Verify that a Team Manager can add and remove users from a team.
    """
    # 1. Setup: Manager and Regular User
    # We need to create a user with MANAGE_TEAMS role
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create and verify manager user
    manager_data = {
        "username": "manager",
        "email": "manager@test.com",
        "password": "password12345",
    }
    await register_and_verify_user(manager_data)

    # Get manager ID (we need to find it, or just use get_by_username if we had it, but we can filter from list)
    # Simpler: just use admin to update roles. We need ID.
    users_res = await client.get("/users", headers=admin_headers)
    users = users_res.json()
    manager_id = next(u["id"] for u in users if u["username"] == "manager")

    # Grant MANAGE_TEAMS role
    await client.patch(
        f"/users/{manager_id}", json={"roles": ["MANAGE_TEAMS"]}, headers=admin_headers
    )

    # Login as manager
    manager_token = await auth_token_factory("manager", "password")
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Get User ID
    user_me_res = await client.get("/users/me", headers=user_headers)
    user_id = user_me_res.json()["id"]

    # 2. Manager creates a team
    create_res = await client.post(
        "/teams",
        json={"name": "Membership Team"},
        headers=manager_headers,
    )
    assert create_res.status_code == 200
    team_id = create_res.json()["id"]

    # 3. Add user to team
    add_res = await client.post(
        f"/teams/{team_id}/members",
        json={"user_id": user_id},
        headers=manager_headers,
    )
    assert add_res.status_code == 200
    team_data = add_res.json()
    assert any(u["id"] == user_id for u in team_data["users"])

    # 4. Remove user from team
    del_res = await client.delete(
        f"/teams/{team_id}/members/{user_id}",
        headers=manager_headers,
    )
    assert del_res.status_code == 200
    team_data = del_res.json()
    assert not any(u["id"] == user_id for u in team_data["users"])


@pytest.mark.asyncio
async def test_team_membership_permissions(client: AsyncClient, auth_token_factory):
    """
    Verify that a regular user cannot add members to a team.
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    user_id = (await client.get("/users/me", headers=user_headers)).json()["id"]

    # Admin creates team
    create_res = await client.post(
        "/teams",
        json={"name": "Protected Team"},
        headers=admin_headers,
    )
    team_id = create_res.json()["id"]

    # User tries to add self to team -> 403
    res = await client.post(
        f"/teams/{team_id}/members",
        json={"user_id": user_id},
        headers=user_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_add_non_existent_member(client: AsyncClient, auth_token_factory):
    """
    Verify 404 when adding a non-existent user.
    """
    token = await auth_token_factory("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/teams",
        json={"name": "Ghost Team"},
        headers=headers,
    )
    team_id = create_res.json()["id"]

    res = await client.post(
        f"/teams/{team_id}/members",
        json={"user_id": 999999},
        headers=headers,
    )
    assert res.status_code == 404
