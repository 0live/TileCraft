from app.core.messages import MessageService

MIN_PASSWORD_LENGTH = 12


def validate_password(password: str) -> str:
    """
    Validate password according to NIST guidelines:
    - Minimum length check.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            MessageService.get_message(
                "validation.password_too_short", length=MIN_PASSWORD_LENGTH
            )
        )

    return password
