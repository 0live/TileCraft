from unittest.mock import AsyncMock, Mock

import pytest
from app.core.config import Settings
from app.core.enums.access_policy import AccessPolicy
from app.core.exceptions import DuplicateEntityException, PermissionDeniedException
from app.modules.teams.schemas import TeamBase
from app.modules.teams.service import TeamService
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail


class TestTeamService:
    @pytest.fixture
    def mock_repo(self):
        repo = Mock()
        repo.session = AsyncMock()
        return repo

    @pytest.fixture
    def mock_settings(self):
        return Settings()

    @pytest.fixture
    def service(self, mock_repo, mock_settings):
        return TeamService(repository=mock_repo, settings=mock_settings)

    @pytest.fixture
    def admin_user(self):
        return UserDetail(
            id=1,
            username="admin",
            email="admin@test.com",
            roles=[UserRole.ADMIN],
            teams=[],
        )

    @pytest.fixture
    def user(self):
        return UserDetail(
            id=2,
            username="user",
            email="user@test.com",
            roles=[UserRole.USER],
            teams=[],
        )

    @pytest.mark.asyncio
    async def test_create_team_success(self, service, mock_repo, admin_user):
        """Test successful team creation by admin."""
        team_base = TeamBase(name="New Team", access_policy=AccessPolicy.STANDARD)
        mock_repo.get_by_name = AsyncMock(return_value=None)

        created_team = Mock(id=10)
        created_team.name = "New Team"
        mock_repo.create = AsyncMock(return_value=created_team)

        expected_detail = Mock(
            id=10,
            access_policy=AccessPolicy.STANDARD,
            created_by_id=admin_user.id,
            users=[],
        )
        expected_detail.name = "New Team"
        mock_repo.get = AsyncMock(return_value=expected_detail)

        result = await service.create_team(team_base, admin_user)

        assert result.name == "New Team"
        mock_repo.create.assert_called_once()
        mock_repo.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_team_permission_denied(self, service, mock_repo, user):
        """Test team creation denied for standard user."""
        team_base = TeamBase(name="New Team")

        with pytest.raises(PermissionDeniedException) as exc:
            await service.create_team(team_base, user)

        assert exc.value.params["detail"] == "team.create_permission_denied"
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_team_duplicate_name(self, service, mock_repo, admin_user):
        """Test team creation with duplicate name."""
        team_base = TeamBase(name="Existing Team")
        mock_repo.get_by_name = AsyncMock(return_value=Mock())

        with pytest.raises(DuplicateEntityException) as exc:
            await service.create_team(team_base, admin_user)

        assert exc.value.key == "team.name_exists"
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_team_by_id_success(self, service, mock_repo, user):
        """Test get team by id success (public)."""
        team = Mock(
            id=10, access_policy=AccessPolicy.PUBLIC, created_by_id=99, users=[]
        )
        team.name = "Public Team"
        mock_repo.get = AsyncMock(return_value=team)

        result = await service.get_team_by_id(10, user)
        assert result.id == 10

    @pytest.mark.asyncio
    async def test_get_team_by_id_private_denied(self, service, mock_repo, user):
        """Test get private team denied."""
        team = Mock(
            id=10, access_policy=AccessPolicy.STANDARD, created_by_id=99, users=[]
        )
        team.name = "Private Team"
        mock_repo.get = AsyncMock(return_value=team)

        with pytest.raises(PermissionDeniedException) as exc:
            await service.get_team_by_id(10, user)

        assert exc.value.params["detail"] == "team.view_permission_denied"

    @pytest.mark.asyncio
    async def test_get_team_member_access(self, service, mock_repo, user):
        """Test access to private team for member."""
        team = Mock(
            id=10,
            access_policy=AccessPolicy.STANDARD,
            created_by_id=99,
            users=[user],  # user is a member
        )
        team.name = "Private Team"
        mock_repo.get = AsyncMock(return_value=team)

        result = await service.get_team_by_id(10, user)
        assert result.id == 10

    @pytest.mark.asyncio
    async def test_update_team_permission_denied(self, service, mock_repo, user):
        """Test update permission denied."""
        team = Mock(id=10)
        team.name = "Team"
        mock_repo.get = AsyncMock(return_value=team)

        update = TeamBase(name="Updated")

        with pytest.raises(PermissionDeniedException) as exc:
            await service.update_team(10, update, user)

        assert exc.value.params["detail"] == "team.update_permission_denied"

    @pytest.mark.asyncio
    async def test_delete_team_success(self, service, mock_repo, admin_user):
        """Test delete team success."""
        team = Mock(id=10)
        mock_repo.get = AsyncMock(return_value=team)
        mock_repo.delete = AsyncMock(return_value=True)

        result = await service.delete_team(10, admin_user)
        assert result is True
        mock_repo.delete.assert_called_once_with(10)
