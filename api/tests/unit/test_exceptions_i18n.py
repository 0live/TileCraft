from app.core.exceptions import (
    APIException,
    AuthenticationException,
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)


class TestExceptionsI18n:
    def test_entity_not_found_exception_defaults(self):
        """Test EntityNotFoundException defaults."""
        exc = EntityNotFoundException(entity="User")
        assert exc.key == "entity.not_found"
        assert exc.params == {"entity": "User"}
        assert str(exc) == "entity.not_found - {'entity': 'User'}"

    def test_entity_not_found_exception_custom_key(self):
        """Test EntityNotFoundException with custom key."""
        exc = EntityNotFoundException(entity="User", key="user.not_found")
        assert exc.key == "user.not_found"
        assert exc.params == {"entity": "User"}
        assert str(exc) == "user.not_found - {'entity': 'User'}"

    def test_entity_not_found_exception_custom_params(self):
        """Test EntityNotFoundException with custom params."""
        exc = EntityNotFoundException(
            entity="User", key="user.not_found", params={"id": 123}
        )
        assert exc.key == "user.not_found"
        assert exc.params == {"entity": "User", "id": 123}

    def test_permission_denied_exception(self):
        """Test PermissionDeniedException."""
        # Default
        exc = PermissionDeniedException()
        assert exc.key == "permission.denied"
        assert exc.params == {}

        # With params
        exc = PermissionDeniedException(params={"detail": "some detail"})
        assert exc.key == "permission.denied"
        assert exc.params == {"detail": "some detail"}

    def test_authentication_exception(self):
        """Test AuthenticationException."""
        # Default
        exc = AuthenticationException()
        assert exc.key == "auth.failed"
        assert exc.params == {}

        # Custom key and params
        exc = AuthenticationException(
            key="auth.invalid_credentials", params={"attempt": 1}
        )
        assert exc.key == "auth.invalid_credentials"
        assert exc.params == {"attempt": 1}

    def test_duplicate_entity_exception(self):
        """Test DuplicateEntityException."""
        exc = DuplicateEntityException(
            key="user.email_exists", params={"email": "a@b.c"}
        )
        assert exc.key == "user.email_exists"
        assert exc.params == {"email": "a@b.c"}

    def test_domain_exception(self):
        """Test generic DomainException."""
        exc = DomainException(key="some.error", params={"info": "test"})
        assert exc.key == "some.error"
        assert exc.params == {"info": "test"}

    def test_api_exception_base(self):
        """Test base APIException behavior."""
        exc = APIException(key="base.error", params={"x": 1})
        assert exc.key == "base.error"
        assert exc.params == {"x": 1}
