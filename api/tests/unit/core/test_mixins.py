from app.core.enums.access_policy import AccessPolicy
from app.core.mixins.access_policy_mixin import AccessPolicyMixin
from app.core.mixins.audit_mixin import AuditMixin


class TestAuditMixin:
    def test_add_audit_info(self):
        """Test manually adding audit info to a dict."""
        data = {"name": "Test"}
        user_id = 99

        result = AuditMixin.add_audit_info(data, user_id)

        assert "created_at" in result
        assert "updated_at" in result
        assert result["created_by_id"] == user_id
        assert result["updated_by_id"] == user_id

    def test_add_audit_info_update(self):
        """Test updating audit info keeps created_at if present."""
        data = {"name": "Test", "created_at": "old", "created_by_id": 1}
        user_id = 99

        result = AuditMixin.add_audit_info(data, user_id)

        assert result["created_at"] == "old"
        assert result["created_by_id"] == 1
        assert "updated_at" in result
        assert result["updated_by_id"] == user_id


class TestAccessPolicyMixin:
    def test_default_access_policy(self):
        """Test default access policy is STANDARD."""
        instance = AccessPolicyMixin()
        assert instance.access_policy == AccessPolicy.STANDARD

    def test_custom_access_policy(self):
        """Test setting custom access policy."""
        instance = AccessPolicyMixin(access_policy=AccessPolicy.PUBLIC)
        assert instance.access_policy == AccessPolicy.PUBLIC
