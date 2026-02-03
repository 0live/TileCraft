from typing import Any, Dict, Optional


class APIException(Exception):
    """Base exception for all API exceptions."""

    def __init__(self, key: str, params: Optional[Dict[str, Any]] = None):
        self.key = key
        self.params = params or {}
        # We don't call super().__init__(message) here because the message is resolved later
        # But for debugging purposes, we can stringify the key and params
        super().__init__(f"{key} - {self.params}")


class DomainException(APIException):
    """Exception raised when a business rule is violated."""

    pass


class EntityNotFoundException(DomainException):
    """Exception raised when an entity is not found via ID or unique attribute."""

    def __init__(
        self,
        entity: str,
        key: str = "entity.not_found",
        params: Optional[Dict[str, Any]] = None,
    ):
        p = params or {}
        p["entity"] = entity
        super().__init__(key=key, params=p)


class PermissionDeniedException(DomainException):
    """Exception raised when a user does not have permission."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(key="permission.denied", params=params)


class AuthenticationException(DomainException):
    """Exception raised when authentication fails."""

    def __init__(
        self, key: str = "auth.failed", params: Optional[Dict[str, Any]] = None
    ):
        super().__init__(key=key, params=params)


class SecurityException(APIException):
    """Exception raised for security configuration errors."""

    def __init__(self, key: str, params: Optional[Dict[str, Any]] = None):
        super().__init__(key=key, params=params)


class DuplicateEntityException(DomainException):
    """Exception raised when an entity already exists."""

    def __init__(self, key: str, params: Optional[Dict[str, Any]] = None):
        super().__init__(key=key, params=params)
