from unittest.mock import Mock, mock_open, patch

import pytest
from app.core.messages import MessageService


class TestMessageService:
    @pytest.fixture(autouse=True)
    def reset_messages(self):
        """Reset messages before each test."""
        MessageService._messages = {}
        MessageService._loaded = False
        yield
        MessageService._messages = {}
        MessageService._loaded = False

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"hello": "world", "nested": {"key": "value"}}',
    )
    def test_load_messages(self, mock_file, mock_listdir, mock_exists):
        """Test loading messages from JSON files."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["en.json"]

        MessageService.load_messages()

        assert MessageService._loaded is True
        assert "en" in MessageService._messages
        assert MessageService._messages["en"]["hello"] == "world"

    @patch("app.core.messages.get_settings")
    def test_get_message_simple(self, mock_settings):
        """Test retrieving a simple message."""
        mock_settings.return_value = Mock(locale="en")
        MessageService._messages = {"en": {"hello": "world"}}
        MessageService._loaded = True

        msg = MessageService.get_message("hello")
        assert msg == "world"

    @patch("app.core.messages.get_settings")
    def test_get_message_nested(self, mock_settings):
        """Test retrieving a nested message via dot notation."""
        mock_settings.return_value = Mock(locale="en")
        MessageService._messages = {"en": {"auth": {"login": "Success"}}}
        MessageService._loaded = True

        msg = MessageService.get_message("auth.login")
        assert msg == "Success"

    @patch("app.core.messages.get_settings")
    def test_get_message_formatting(self, mock_settings):
        """Test message formatting with kwargs."""
        mock_settings.return_value = Mock(locale="en")
        MessageService._messages = {"en": {"welcome": "Hello {name}"}}
        MessageService._loaded = True

        msg = MessageService.get_message("welcome", name="Olivier")
        assert msg == "Hello Olivier"

    @patch("app.core.messages.get_settings")
    def test_get_message_not_found(self, mock_settings):
        """Test message not found returns error string."""
        mock_settings.return_value = Mock(locale="en")
        MessageService._messages = {"en": {}}
        MessageService._loaded = True

        msg = MessageService.get_message("missing.key")
        assert "Message not found" in msg

    @patch("app.core.messages.get_settings")
    def test_get_message_fallback(self, mock_settings):
        """Test fallback to english if locale missing."""
        mock_settings.return_value = Mock(locale="fr")
        MessageService._messages = {"en": {"hello": "world"}}
        MessageService._loaded = True

        msg = MessageService.get_message("hello")
        # Should fall back to EN because FR is missing from loaded messages
        assert msg == "world"
