import pytest
from app.core.enums.access_policy import AccessPolicy
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_team_visibility_for_member(client: AsyncClient, auth_token_factory):
    """
    Verify that a regular user can see teams they belong to,
    and cannot see private teams they are not a member of.
    """
    # 1. Login as Admin and seeded 'user'
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 'user' is already seeded and is in 'Atlas viewer' team (team2)
    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Login as 'editor' who is not in 'Atlas viewer' team
    editor_token = await auth_token_factory("editor", "editor")
    editor_headers = {"Authorization": f"Bearer {editor_token}"}

    # 2. Get user info
    user_id = (await client.get("/users/me", headers=user_headers)).json()["id"]

    # 3. Admin creates a private team
    create_res = await client.post(
        "/teams",
        json={"name": "Private Team"},
        headers=admin_headers,
    )
    assert create_res.status_code == 200
    team_data = create_res.json()
    team_id = team_data["id"]

    # 4. Admin adds 'user' to the team
    await client.patch(
        f"/users/{user_id}",
        json={"teams": [team_id]},
        headers=admin_headers,
    )

    # 5. User requests all teams -> should see it
    res = await client.get("/teams", headers=user_headers)
    assert res.status_code == 200
    teams = res.json()
    assert any(t["id"] == team_id for t in teams)

    # 6. Editor (stranger) requests all teams -> should NOT see it
    res = await client.get("/teams", headers=editor_headers)
    assert res.status_code == 200
    teams_editor = res.json()
    assert not any(t["id"] == team_id for t in teams_editor)


@pytest.mark.asyncio
async def test_team_modification_permission(client: AsyncClient, auth_token_factory):
    """
    Verify that a regular user (even a member) cannot update or delete a team
    they do not own (and lack MANAGE_TEAMS role).
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    user_id = (await client.get("/users/me", headers=user_headers)).json()["id"]

    # Admin creates team
    create_res = await client.post(
        "/teams",
        json={"name": "Team Mod Test"},
        headers=admin_headers,
    )
    team_id = create_res.json()["id"]

    # Admin adds member
    await client.patch(
        f"/users/{user_id}",
        json={"teams": [team_id]},
        headers=admin_headers,
    )

    # Member tries update -> Should fail
    update_res = await client.patch(
        f"/teams/{team_id}",
        json={"name": "Hacked Team"},
        headers=user_headers,
    )
    assert update_res.status_code == 403

    # Member tries delete -> Should fail
    delete_res = await client.delete(f"/teams/{team_id}", headers=user_headers)
    assert delete_res.status_code == 403


@pytest.mark.asyncio
async def test_atlas_public_private_access(client: AsyncClient, auth_token_factory):
    """
    Verify visibility of public vs private atlases.
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 'user' is a regular user
    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Admin creates Standard (Private) Atlas
    priv_res = await client.post(
        "/atlases",
        json={"name": "Private Atlas", "description": "Hidden"},
        headers=admin_headers,
    )
    priv_id = priv_res.json()["id"]

    # Admin creates Public Atlas
    pub_res = await client.post(
        "/atlases",
        json={"name": "Public Atlas", "description": "Open"},
        headers=admin_headers,
    )
    pub_id = pub_res.json()["id"]
    await client.patch(
        f"/atlases/{pub_id}",
        json={"access_policy": AccessPolicy.PUBLIC},
        headers=admin_headers,
    )

    # User tries to get Private -> 404
    res = await client.get(f"/atlases/{priv_id}", headers=user_headers)
    assert res.status_code == 404

    # User tries to get Public -> 200
    res = await client.get(f"/atlases/{pub_id}", headers=user_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_atlas_team_access(client: AsyncClient, auth_token_factory):
    """
    Verify that linking a team to an atlas grants view access.
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    user_id = (await client.get("/users/me", headers=user_headers)).json()["id"]

    # Create Atlas
    atlas_res = await client.post(
        "/atlases",
        json={"name": "Team Atlas", "description": "desc"},
        headers=admin_headers,
    )
    atlas_id = atlas_res.json()["id"]

    # Create Team
    team_res = await client.post(
        "/teams",
        json={"name": "Access Team"},
        headers=admin_headers,
    )
    team_id = team_res.json()["id"]

    # Link Team to Atlas
    await client.post(
        "/atlases/team",
        json={"atlas_id": atlas_id, "team_id": team_id},
        headers=admin_headers,
    )

    # Verify User CANNOT see atlas yet
    res = await client.get(f"/atlases/{atlas_id}", headers=user_headers)
    assert res.status_code == 404

    # Add User to Team
    await client.patch(
        f"/users/{user_id}",
        json={"teams": [team_id]},
        headers=admin_headers,
    )

    # Verify User CAN see atlas now
    res = await client.get(f"/atlases/{atlas_id}", headers=user_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_atlas_management_permission(client: AsyncClient, auth_token_factory):
    """
    Verify 'can_manage_atlas' permission in team link.
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    # User is already in some teams, let's reset or just create new team/atlas context
    user_id = (await client.get("/users/me", headers=user_headers)).json()["id"]

    # Create Atlas & Team
    atlas_id = (
        await client.post(
            "/atlases",
            json={"name": "Managable Atlas", "description": "d"},
            headers=admin_headers,
        )
    ).json()["id"]
    team_id = (
        await client.post(
            "/teams", json={"name": "Manager Team"}, headers=admin_headers
        )
    ).json()["id"]

    # Add User to Team
    await client.patch(
        f"/users/{user_id}", json={"teams": [team_id]}, headers=admin_headers
    )

    # Link with NO manage permission
    await client.post(
        "/atlases/team",
        json={"atlas_id": atlas_id, "team_id": team_id, "can_manage_atlas": False},
        headers=admin_headers,
    )

    # User tries to update -> 403
    res = await client.patch(
        f"/atlases/{atlas_id}", json={"description": "Hacked"}, headers=user_headers
    )
    assert res.status_code == 403

    # Update Link to GRANT manage permission
    await client.post(
        "/atlases/team",
        json={"atlas_id": atlas_id, "team_id": team_id, "can_manage_atlas": True},
        headers=admin_headers,
    )

    # User tries to update -> 200
    res = await client.patch(
        f"/atlases/{atlas_id}",
        json={"description": "Legit Update"},
        headers=user_headers,
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_map_creation_permission(client: AsyncClient, auth_token_factory):
    """
    Verify 'can_create_maps' permission.
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    user_token = await auth_token_factory("user", "user")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    user_id = (await client.get("/users/me", headers=user_headers)).json()["id"]

    # Create Atlas & Team
    atlas_id = (
        await client.post(
            "/atlases",
            json={"name": "Map Atlas", "description": "d"},
            headers=admin_headers,
        )
    ).json()["id"]
    team_id = (
        await client.post("/teams", json={"name": "Mapper Team"}, headers=admin_headers)
    ).json()["id"]
    await client.patch(
        f"/users/{user_id}", json={"teams": [team_id]}, headers=admin_headers
    )

    # Link with NO create permission
    await client.post(
        "/atlases/team",
        json={"atlas_id": atlas_id, "team_id": team_id, "can_create_maps": False},
        headers=admin_headers,
    )

    # User tries create map -> 403
    map_payload = {
        "name": "New Map",
        "style": "dark",
        "description": "Test Map",
        "atlas_id": atlas_id,
    }
    res = await client.post("/maps", json=map_payload, headers=user_headers)
    assert res.status_code == 403

    # Grant permission
    await client.post(
        "/atlases/team",
        json={"atlas_id": atlas_id, "team_id": team_id, "can_create_maps": True},
        headers=admin_headers,
    )

    # Connect again to update permissions
    res = await client.post("/maps", json=map_payload, headers=user_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_role_manage_atlases_limitation(client: AsyncClient, auth_token_factory):
    """
    Verify that a user with MANAGE_ATLASES_AND_MAPS role CANNOT view/edit
    private atlases created by others (unlike ADMIN).
    """
    admin_token = await auth_token_factory("admin", "admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Register a new user to start clean for this role test,
    # instead of messing with seeded 'editor'.
    # Although the directive says "use seeded", creating a fresh one for specific role mutation
    # is safer to avoid side effects on other tests running in parallel (though pytest-asyncio runs sequentially mostly)
    # But let's stick to creating one via Admin if we can, or register.
    # Actually, seeded 'editor' HAS this role. Let's use it!
    # "roles=[UserRole.USER, UserRole.MANAGE_ATLASES_AND_MAPS]" -> existing 'editor'
    manager_token = await auth_token_factory("editor", "editor")
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    # 2. 'user' creates a Private Atlas (as they are a regular user, they can create?)
    # Wait, usually regular creation depends on policy. User role usually can create?
    # Actually `test_atlases.py` creates as Admin.
    # Let's check permissions for standard user creating atlas.
    # `AtlasService.create_atlas` checks:
    # if all(role not in current_user.roles for role in [ADMIN, MANAGE_ATLASES_AND_MAPS]): raise PermissionDenied
    # So regular 'user' CANNOT create atlases. Only Admin or Editor.

    # So we need Admin to create an atlas "owned" by someone else?
    # Or create a NEW user with MANAGE_ATLASES permission but distinct from 'editor'.
    # Or simpler: Admin creates an atlas. Editor should check if they can access it.
    # Admin is "super". Atlas created by Admin is owned by Admin.
    # Editor (MANAGE_ATLASES_AND_MAPS) should NOT access Admin's private atlas?
    # Logic in service:
    # can_view = (Admin or CreatedBy or Public or TeamLink)
    # It does NOT say "or MANAGE_ATLASES role".
    # So Editor CANNOT view Admin's private atlas. Correct.

    # Create Private Atlas by Admin
    res_admin = await client.post(
        "/atlases",
        json={"name": "Admin Private Atlas", "description": "Mine"},
        headers=admin_headers,
    )
    atlas_id = res_admin.json()["id"]

    # Manager (Editor) tries to GET -> Should fail (404)
    res = await client.get(f"/atlases/{atlas_id}", headers=manager_headers)
    assert res.status_code == 404

    # Manager tries to UPDATE -> Should fail
    res = await client.patch(
        f"/atlases/{atlas_id}", json={"description": "Stolen"}, headers=manager_headers
    )
    assert res.status_code in [403, 404]
