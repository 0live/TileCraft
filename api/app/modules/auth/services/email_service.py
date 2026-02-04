from email.message import EmailMessage

import aiosmtplib

from app.core.config import Settings
from app.core.exceptions import EmailSendException
from app.core.logging_config import logger
from app.core.messages import MessageService


class EmailService:
    """
    Email Service for sending verification and notification emails.
    Uses aiosmtplib for async SMTP communication.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_verification_email(self, email: str, token: str) -> None:
        """
        Send a verification email to the user with a clickable link.
        """
        site_address = self.settings.site_address or "http://localhost:3000"
        verification_link = f"{site_address.rstrip('/')}/verify?token={token}"

        subject = MessageService.get_message(
            "email.verification_subject", self.settings.locale
        )
        body = self._build_verification_body(verification_link)

        await self._send_email(
            to_email=email,
            subject=subject,
            body=body,
        )

    async def _send_email(self, to_email: str, subject: str, body: str) -> None:
        """
        Send an email using SMTP settings from configuration.
        """
        message = EmailMessage()
        message["From"] = self.settings.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user,
                password=self.settings.smtp_password,
                use_tls=self.settings.smtp_use_tls,
                start_tls=self.settings.smtp_starttls,
            )
            logger.info(f"Email sent successfully to {to_email}")
        except aiosmtplib.SMTPException as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise EmailSendException(params={"recipient": to_email, "error": str(e)})

    def _build_verification_body(self, verification_link: str) -> str:
        """Build the email body for verification emails."""
        locale = self.settings.locale
        greeting = MessageService.get_message("email.verification_greeting", locale)
        instruction = MessageService.get_message(
            "email.verification_instruction", locale
        )
        ignore = MessageService.get_message("email.verification_ignore", locale)

        return f"{greeting}\n\n{instruction}\n\n{verification_link}\n\n{ignore}"
