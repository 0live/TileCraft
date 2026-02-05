import pytest
from app.modules.users.models import User
from httpx import AsyncClient
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
async def test_refresh_token_flow(
    client: AsyncClient, session: AsyncSession, existing_users
):  # 1. Login with seeded user (from seeds.py: user/user)
    username = existing_users[0]["username"]
    password = existing_users[0]["password"]

    login_data = {"username": username, "password": password}
    response = await client.post("/auth/login", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Check Cookie
    assert "refresh_token" in response.cookies
    refresh_token_cookie = response.cookies["refresh_token"]
    assert refresh_token_cookie is not None

    # 2. Access protected endpoint with access token
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    resp_me = await client.get("/users/me", headers=headers)
    assert resp_me.status_code == 200
    assert resp_me.json()["username"] == username

    # 3. Refresh Access Token
    # Send refresh request with cookie
    resp_refresh = await client.post(
        "/auth/refresh", cookies={"refresh_token": refresh_token_cookie}
    )
    assert resp_refresh.status_code == 200
    new_data = resp_refresh.json()
    assert "access_token" in new_data
    assert new_data["access_token"] != data["access_token"]

    # Check new cookie set (Rotation)
    assert "refresh_token" in resp_refresh.cookies
    new_refresh_cookie = resp_refresh.cookies["refresh_token"]
    assert new_refresh_cookie != refresh_token_cookie

    # 4. Logout
    resp_logout = await client.post(
        "/auth/logout", cookies={"refresh_token": new_refresh_cookie}
    )
    assert resp_logout.status_code == 200

    # 5. Try Refresh with old cookie (Should fail - Revoked)
    resp_fail = await client.post(
        "/auth/refresh", cookies={"refresh_token": refresh_token_cookie}
    )
    assert resp_fail.status_code == 401


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, session: AsyncSession):
    # 1. Register
    register_data = {
        "email": "verify@test.com",
        "username": "verify_user",
        "password": "password12345",
    }
    resp_reg = await client.post("/auth/register", json=register_data)
    assert resp_reg.status_code == 200
    user_data = resp_reg.json()
    user_id = user_data["id"]

    # Check DB - is_verified=False
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user_db = result.scalars().first()
    assert user_db.is_verified is False
    assert user_db.verification_token is not None
    token = user_db.verification_token

    # 2. Verify Email
    resp_verify = await client.get(f"/auth/verify?token={token}")
    assert resp_verify.status_code == 200
    assert resp_verify.json()["message"] == "Account verified successfully"

    # 3. Check DB - is_verified=True
    # Need to refresh or re-query
    session.expire_all()
    user_db = await session.get(User, user_id)
    assert user_db.is_verified is True
    assert user_db.verification_token is None
