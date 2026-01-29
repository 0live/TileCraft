from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from app.core.repository import BaseRepository
from sqlmodel import SQLModel


class MockModel(SQLModel):
    id: int
    name: str


class TestBaseRepository:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repository(self, mock_session):
        # We ensure MockModel has the attributes for the queries
        MockModel.id = 1
        MockModel.name = "name"
        return BaseRepository(session=mock_session, model=MockModel)

    @pytest.mark.asyncio
    async def test_create(self, repository, mock_session):
        """Test creating an entity."""
        attributes = {"name": "Test Item", "id": 1}

        result = await repository.create(attributes)

        assert result.name == "Test Item"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_get(self, mock_select, repository, mock_session):
        """Test getting an entity by ID."""
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        # Mock options chaining
        mock_query.where.return_value = mock_query
        mock_query.options.return_value = mock_query

        mock_result = Mock()
        mock_result.first.return_value = MockModel(id=1, name="Found")
        mock_session.exec.return_value = mock_result

        result = await repository.get(1)

        assert result.id == 1
        assert result.name == "Found"
        # Verify construction
        mock_select.assert_called_with(MockModel)
        mock_query.where.assert_called_once()
        mock_session.exec.assert_called_once_with(mock_query)

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_get_all(self, mock_select, repository, mock_session):
        """Test getting all entities."""
        mock_query = MagicMock()
        mock_select.return_value = mock_query

        mock_result = Mock()
        mock_result.all.return_value = [
            MockModel(id=1, name="1"),
            MockModel(id=2, name="2"),
        ]
        mock_session.exec.return_value = mock_result

        result = await repository.get_all()

        assert len(result) == 2
        mock_select.assert_called_with(MockModel)
        mock_session.exec.assert_called_once_with(mock_query)

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_update_success(self, mock_select, repository, mock_session):
        """Test updating an entity."""
        # Mock introspection to avoid SQLAlchemy inspection issues
        repository._get_relationship_fields = Mock(return_value=set())

        # Setup mocks for get()
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        existing_obj = MockModel(id=1, name="Old")
        mock_result = Mock()
        mock_result.first.return_value = existing_obj
        mock_session.exec.return_value = mock_result

        result = await repository.update(1, {"name": "New"})

        assert result.name == "New"
        mock_session.add.assert_called_with(existing_obj)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_update_not_found(self, mock_select, repository, mock_session):
        """Test updating a non-existent entity."""
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await repository.update(999, {"name": "New"})

        assert result is None
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_delete_success(self, mock_select, repository, mock_session):
        """Test successful deletion."""
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        existing_obj = MockModel(id=1, name="To Delete")
        mock_result = Mock()
        mock_result.first.return_value = existing_obj
        mock_session.exec.return_value = mock_result

        result = await repository.delete(1)

        assert result is True
        mock_session.delete.assert_called_with(existing_obj)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_delete_not_found(self, mock_select, repository, mock_session):
        """Test deletion of missing entity."""
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await repository.delete(999)

        assert result is False
        mock_session.delete.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.core.repository.select")
    async def test_get_by_name(self, mock_select, repository, mock_session):
        """Test get by name."""
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        mock_result = Mock()
        mock_result.first.return_value = MockModel(id=1, name="Target")
        mock_session.exec.return_value = mock_result

        result = await repository.get_by_name("Target")

        assert result.name == "Target"
        mock_session.exec.assert_called_once()
