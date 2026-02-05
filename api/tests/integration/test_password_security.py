import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_weak_password_short(client: AsyncClient, user_data):
    """Test registration with a short password fails."""
    user_data["password"] = "shortpass"  # 9 chars
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 422
    data = response.json()

    # Custom error structure: params -> errors
    errors = data.get("params", {}).get("errors", [])
    assert len(errors) > 0

    found_error = False
    for error in errors:
        msg = error.get("msg", "")
        if "password" in msg.lower() or "caractères" in msg or "characters" in msg:
            found_error = True
            break

    assert found_error, f"Password too short error not found in {errors}"
