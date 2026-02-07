from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_import_endpoint_admin_only(client: AsyncClient, auth_token_factory):
    # Mock ImportService to avoid actual processing
    with patch(
        "app.modules.import_data.endpoints.ImportService.create_import_task"
    ) as mock_create:
        mock_create.return_value = {"task_id": "123", "status": "processing"}

        # 1. Test with Normal User -> Should fail (403)
        user_token = await auth_token_factory(username="user", password="user")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        files = {"file": ("test.geojson", b"{}", "application/geo+json")}
        data = {"table_name": "test_table", "schema": "geodata"}

        response = await client.post(
            "/import", files=files, data=data, headers=user_headers
        )
        assert response.status_code == 403

        # 2. Test with Admin User -> Should succeed (202)
        admin_token = await auth_token_factory(username="admin", password="admin")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        files = {"file": ("test.geojson", b"{}", "application/geo+json")}

        response = await client.post(
            "/import", files=files, data=data, headers=admin_headers
        )
        assert response.status_code == 202
        assert response.json() == {"task_id": "123", "status": "processing"}
