from app.models.users import UserRead
from fastapi.testclient import TestClient


def test_create_user(client: TestClient, user_data):
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    # Validate with Pydantic model
    user_out = UserRead(**data)
    assert user_out.email == user_data["email"]
    assert "password" not in data
    assert "hashed_password" not in data


def test_get_all_users_permissions(
    client: TestClient, auth_token_factory, existing_users
):
    """Tests access control for listing all users."""
    # 1. Unauthenticated
    assert client.get("/users").status_code == 401

    # 2. Authenticated as regular user (Should be Forbidden)
    token = auth_token_factory(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    # 3. Authenticated as admin (Should be OK)
    admin_token = auth_token_factory(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )
    response = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user_dynamic_id(client: TestClient, auth_token_factory, existing_users):
    """Tests retrieving a user with a dynamic ID instead of hardcoded '1'."""
    admin_token = auth_token_factory(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )

    # Get own ID first
    me_res = client.get("/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    my_id = me_res.json()["id"]

    # Fetch user by dynamic ID
    response = client.get(
        f"/users/{my_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == existing_users[2]["username"]


def test_update_user_role_restriction(
    client: TestClient, auth_token_factory, user_data
):
    """Verifies that a user cannot upgrade their own roles."""
    client.post("/users/register", json=user_data)
    token = auth_token_factory(
        username=user_data["username"], password=user_data["password"]
    )

    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    user_id = me["id"]

    # Attempting to change roles should fail
    updated_data = {"roles": ["ADMIN"]}
    response = client.patch(
        f"/users/{user_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    # Changed from 401 to 403 as the user is authenticated but not authorized
    assert response.status_code == 403
