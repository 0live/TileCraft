from fastapi.testclient import TestClient


def test_create_user(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "test@test.com",
            "username": "test_user",
            "password": "test_password",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["id"] is not None
    assert data["email"] == "test@test.com"
    assert data["username"] == "test_user"
    assert "password" not in data
    assert "hashed_password" not in data
    assert "USER" in data["roles"]
    assert "teams" in data


def test_get_all_users(client: TestClient):
    response = client.get("/users")
    assert response.status_code == 401
