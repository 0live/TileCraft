import pytest
from app.core.enums.access_policy import AccessPolicy
from app.modules.teams.models import Team
from app.modules.teams.repository import TeamRepository
from app.modules.users.models import User
from sqlmodel import select


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_repository_flush_behavior(session, user_data):
    """
    Verify that repository operations only flush and do not commit,
    allowing for manual rollback by the service layer.
    """
    # 1. Setup Repository
    repo = TeamRepository(session, Team)

    # Fetch a valid user
    user_result = await session.exec(select(User))
    user = user_result.first()
    assert user is not None, "Seeder should have created users"

    # 2. Create a Team (implicitly flush-only)
    team_data = {
        "name": "Rolled Back Team",
        "description": "Should not exist",
        "created_by_id": user.id,
        "access_policy": AccessPolicy.STANDARD,
    }

    # This should flush but not commit
    team = await repo.create(team_data)

    assert team.id is not None
    assert team.name == "Rolled Back Team"

    # 3. Verify it is visible in the current transaction (session)
    # We use a direct SQL check on the same connection to verify it's flushed
    result = await session.exec(select(Team).where(Team.name == "Rolled Back Team"))
    fetched_team = result.first()
    assert fetched_team is not None

    # 4. Rollback
    await session.rollback()

    # 5. Verify it is GONE
    # Note: After rollback, the session is expired/rolled back.
    # We can check again.
    result_after = await session.exec(
        select(Team).where(Team.name == "Rolled Back Team")
    )
    fetched_team_after = result_after.first()

    assert fetched_team_after is None
