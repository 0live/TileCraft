from app.core.logging_config import logger


class EmailService:
    """
    Mock Email Service for sending verification emails.
    In production, this would connect to an SMTP server or API (SendGrid, SES, etc.).
    """

    @staticmethod
    async def send_verification_email(email: str, token: str) -> None:
        """
        Send a verification email to the user.
        For now, we just log the link.
        """
        # TODO: Get frontend URL from settings
        verification_link = f"http://localhost:3000/verify?token={token}"

        logger.info("=======================================================")
        logger.info(f"EMAIL TO: {email}")
        logger.info("SUBJECT: Verify your account")
        logger.info(f"CONTENT: Click here to verify: {verification_link}")
        logger.info("=======================================================")
