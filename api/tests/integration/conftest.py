from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_email_service():
    """Mock EmailService to avoid actual SMTP connections during integration tests."""
    with patch(
        "app.modules.auth.services.email_service.EmailService.send_verification_email",
        new_callable=AsyncMock,
    ) as mock:
        yield mock
