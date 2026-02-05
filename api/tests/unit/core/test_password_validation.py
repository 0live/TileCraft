import pytest
from app.core.password_validation import validate_password


def test_validate_password_valid():
    """Test that a valid password passes validation."""
    password = "correcthorsebatterystaple"
    assert validate_password(password) == password


def test_validate_password_too_short():
    """Test that a short password raises ValueError."""
    with pytest.raises(ValueError):
        validate_password("short_pwd")  # 9 chars, < 12
