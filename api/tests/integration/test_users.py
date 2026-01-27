import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_all_users_permissions(
    client: AsyncClient, auth_token_factory, existing_users
):
    """Tests access control for listing all users."""
    # 1. Unauthenticated
    response = await client.get("/users")
    assert response.status_code == 401

    # 2. Authenticated as regular user (Should be Forbidden)
    token = await auth_token_factory(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    response = await client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    # 3. Authenticated as admin (Should be OK)
    admin_token = await auth_token_factory(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )
    response = await client.get(
        "/users", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_user_dynamic_id(
    client: AsyncClient, auth_token_factory, existing_users
):
    """Tests retrieving a user with a dynamic ID instead of hardcoded '1'."""
    admin_token = await auth_token_factory(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )

    # Get own ID first
    me_res = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {admin_token}"}
    )
    my_id = me_res.json()["id"]

    # Fetch user by dynamic ID
    response = await client.get(
        f"/users/{my_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == existing_users[2]["username"]


@pytest.mark.asyncio
async def test_update_user_role_restriction(
    client: AsyncClient, auth_token_factory, user_data
):
    """Verifies that a user cannot upgrade their own roles."""
    # Register via /auth/register
    await client.post("/auth/register", json=user_data)
    token = await auth_token_factory(
        username=user_data["username"], password=user_data["password"]
    )

    me_res = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    me = me_res.json()
    user_id = me["id"]

    # Attempting to change roles should fail
    updated_data = {"roles": ["ADMIN"]}
    response = await client.patch(
        f"/users/{user_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, auth_token_factory, existing_users):
    """Verifies that an admin can delete a user."""
    # 1. Login as Admin
    admin_token = await auth_token_factory(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )

    # 2. Create a dummy user to delete using /auth/register
    user_to_delete = {
        "username": "todelete",
        "email": "todelete@example.com",
        "password": "password",
    }
    await client.post("/auth/register", json=user_to_delete)

    # 3. Get the user ID
    # Usually we'd need to fetch by username or list, let's list them
    list_res = await client.get(
        "/users", headers={"Authorization": f"Bearer {admin_token}"}
    )
    users = list_res.json()
    target_user = next(u for u in users if u["username"] == "todelete")
    target_id = target_user["id"]

    # 4. Delete the user
    del_res = await client.delete(
        f"/users/{target_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 200

    # 5. Verify 404 on get
    get_res = await client.get(
        f"/users/{target_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_update_user_self(client: AsyncClient, auth_token_factory, user_data):
    """Verifies that a user can update their own username and email."""
    # Register via /auth/register
    await client.post("/auth/register", json=user_data)
    token = await auth_token_factory(
        username=user_data["username"], password=user_data["password"]
    )

    # Get own ID
    me_res = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    me = me_res.json()
    user_id = me["id"]

    # Update username and email
    updated_data = {
        "username": "newusername",
        "email": "newemail@example.com",
    }
    response = await client.patch(
        f"/users/{user_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newusername"
    assert data["email"] == "newemail@example.com"

    # Verify updates are persisted
    # Note: Token might be invalidated if it contains the old username.
    # So we re-login with the new username/password to get a fresh token.
    # The password hasn't changed.
    new_token = await auth_token_factory(
        username="newusername", password=user_data["password"]
    )

    me_res_after = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {new_token}"}
    )
    assert me_res_after.status_code == 200
    assert me_res_after.json()["username"] == "newusername"
