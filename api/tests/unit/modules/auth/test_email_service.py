from unittest.mock import AsyncMock, patch

import pytest
from aiosmtplib import SMTPException
from app.core.config import Settings
from app.core.exceptions import EmailSendException
from app.modules.auth.services.email_service import EmailService


class TestEmailService:
    @pytest.fixture
    def dev_settings(self):
        """Settings for local development (Mailpit)."""
        return Settings(
            site_address="http://localhost:3000",
            smtp_host="localhost",
            smtp_port=1025,
            smtp_from_email="noreply@canopy.dev",
            smtp_use_tls=False,
            smtp_starttls=False,
            locale="en",
        )

    @pytest.fixture
    def prod_settings(self):
        """Settings for production SMTP."""
        return Settings(
            site_address="https://canopy.example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secure_password",
            smtp_from_email="noreply@canopy.example.com",
            smtp_use_tls=False,
            smtp_starttls=True,
            locale="en",
        )

    @pytest.fixture
    def email_service(self, dev_settings):
        return EmailService(dev_settings)

    # =========================================================================
    # send_verification_email Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, email_service):
        """Test successful verification email sending."""
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await email_service.send_verification_email(
                "user@example.com", "test_token_123"
            )

            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs

            assert call_kwargs["hostname"] == "localhost"
            assert call_kwargs["port"] == 1025
            assert call_kwargs["use_tls"] is False
            assert call_kwargs["start_tls"] is False

    @pytest.mark.asyncio
    async def test_send_verification_email_with_credentials(self, prod_settings):
        """Test email sending with SMTP authentication."""
        service = EmailService(prod_settings)

        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await service.send_verification_email("user@example.com", "token")

            call_kwargs = mock_send.call_args.kwargs

            assert call_kwargs["hostname"] == "smtp.example.com"
            assert call_kwargs["port"] == 587
            assert call_kwargs["username"] == "user@example.com"
            assert call_kwargs["password"] == "secure_password"
            assert call_kwargs["start_tls"] is True

    @pytest.mark.asyncio
    async def test_send_verification_email_smtp_failure(self, email_service):
        """Test that SMTP failure raises EmailSendException."""
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = SMTPException("Connection refused")

            with pytest.raises(EmailSendException) as exc:
                await email_service.send_verification_email("user@example.com", "token")

            assert exc.value.params["recipient"] == "user@example.com"
            assert "Connection refused" in exc.value.params["error"]

    # =========================================================================
    # Email Content Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_verification_link_format(self, dev_settings):
        """Test verification link is correctly formatted."""
        service = EmailService(dev_settings)

        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await service.send_verification_email("user@example.com", "abc123")

            message = mock_send.call_args.args[0]
            body = message.get_content()

            assert "http://localhost:3000/verify?token=abc123" in body

    @pytest.mark.asyncio
    async def test_email_headers(self, email_service):
        """Test email headers are correctly set."""
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await email_service.send_verification_email("user@example.com", "token")

            message = mock_send.call_args.args[0]

            assert message["From"] == "noreply@canopy.dev"
            assert message["To"] == "user@example.com"
            assert message["Subject"] == "Verify your Canopy account"
