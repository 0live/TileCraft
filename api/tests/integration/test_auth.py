import pytest
from app.modules.users.schemas import UserRead
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, user_data):
    """Test user registration via /auth/register."""
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    user_out = UserRead(**data)
    assert user_out.email == user_data["email"]
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_login(client: AsyncClient, auth_token_factory, existing_users):
    """Test login via /auth/login."""
    token = await auth_token_factory(
        username=existing_users[0]["username"], password=existing_users[0]["password"]
    )
    assert token is not None
    assert len(token) > 0
