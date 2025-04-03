from fastapi.testclient import TestClient


def test_create_user(client: TestClient, user_data):
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["email"] == "test@test.com"
    assert data["username"] == "test_user"
    assert "password" not in data
    assert "hashed_password" not in data
    assert "USER" in data["roles"]
    assert "teams" in data


def test_login(existing_users, client: TestClient):
    response = client.post(
        "/users/login",
        data={
            "username": existing_users[0]["username"],
            "password": existing_users[0]["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/users/login",
        data={"username": "unknown", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_create_user_duplicate_email(client: TestClient, existing_users):
    response = client.post(
        "/users/register",
        json={
            "email": existing_users[0]["email"],
            "username": "Random",
            "password": "Random",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_create_user_duplicate_username(client: TestClient, existing_users):
    response = client.post(
        "/users/register",
        json={
            "email": "random@random.com",
            "username": existing_users[0]["username"],
            "password": "Random",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_get_all_users(client: TestClient, get_token, existing_users):
    # unauthenticated
    response = client.get("/users")
    assert response.status_code == 401

    # authenticated as user
    token = get_token(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    # authenticated as admin
    token = get_token(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_me(client: TestClient, get_token, existing_users):
    token = get_token(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == existing_users[0]["username"]
    assert data["email"] == existing_users[0]["email"]
    assert "password" not in data
    assert "hashed_password" not in data
    assert "USER" in data["roles"]
    assert "teams" in data


def test_get_user(client: TestClient, get_token, existing_users):
    # get your own user
    token = get_token(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    id = response.json()["id"]
    response = client.get(f"/users/{id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # get another user as admin
    token = get_token(
        username=existing_users[2]["username"], password=existing_users[2]["password"]
    )
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # get another user as user
    token = get_token(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_update_user(client: TestClient, get_token, user_data):
    client.post("/users/register", json=user_data)
    token = get_token(username=user_data["username"], password=user_data["password"])
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    id = response.json()["id"]
    updated_data = {"username": "updated_user", "email": "updated@test.com"}
    response = client.patch(
        f"/users/{id}", json=updated_data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    updated_data = {"roles": ["MANAGE_TEAMS"]}
    response = client.patch(
        f"/users/{id}", json=updated_data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
