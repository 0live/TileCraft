"""
Centralized permission checking utilities.
"""

from app.modules.users.models import UserRole
from app.modules.users.schemas import UserDetail


def has_any_role(user: UserDetail, roles: list[UserRole]) -> bool:
    """Check if user has at least one of the specified roles."""
    return any(role in user.roles for role in roles)


def has_all_roles(user: UserDetail, roles: list[UserRole]) -> bool:
    """Check if user has all of the specified roles."""
    return all(role in user.roles for role in roles)
