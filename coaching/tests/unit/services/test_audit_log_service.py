"""Unit tests for AuditLogService."""

from datetime import UTC, datetime

import pytest
from coaching.src.services.audit_log_service import (
    AuditAction,
    AuditLogEntry,
    AuditLogService,
)


@pytest.mark.unit
class TestAuditLogServiceInit:
    """Test AuditLogService initialization."""

    def test_init_creates_instance(self):
        """Test that service initializes correctly."""
        # Act
        service = AuditLogService()

        # Assert
        assert service is not None


@pytest.mark.unit
class TestAuditLogEntry:
    """Test AuditLogEntry model."""

    def test_create_audit_log_entry_with_required_fields(self):
        """Test creating audit log entry with required fields."""
        # Arrange & Act
        entry = AuditLogEntry(
            action=AuditAction.TEMPLATE_CREATED,
            user_id="user-123",
            tenant_id="tenant-456",
            resource_type="template",
            resource_id="goal_alignment/1.0.0",
        )

        # Assert
        assert entry.action == AuditAction.TEMPLATE_CREATED
        assert entry.user_id == "user-123"
        assert entry.tenant_id == "tenant-456"
        assert entry.resource_type == "template"
        assert entry.resource_id == "goal_alignment/1.0.0"
        assert entry.details == {}
        assert entry.ip_address is None
        assert entry.user_agent is None
        assert isinstance(entry.timestamp, datetime)

    def test_create_audit_log_entry_with_all_fields(self):
        """Test creating audit log entry with all fields."""
        # Arrange
        timestamp = datetime.now(UTC)

        # Act
        entry = AuditLogEntry(
            timestamp=timestamp,
            action=AuditAction.TEMPLATE_UPDATED,
            user_id="user-123",
            tenant_id="tenant-456",
            resource_type="template",
            resource_id="goal_alignment/1.0.0",
            details={"changes": {"system_prompt": "updated"}},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        # Assert
        assert entry.timestamp == timestamp
        assert entry.details == {"changes": {"system_prompt": "updated"}}
        assert entry.ip_address == "192.168.1.1"
        assert entry.user_agent == "Mozilla/5.0"


@pytest.mark.unit
class TestAuditAction:
    """Test AuditAction enum."""

    def test_audit_action_values(self):
        """Test that all audit action values are defined."""
        # Assert
        assert AuditAction.TEMPLATE_CREATED.value == "template_created"
        assert AuditAction.TEMPLATE_UPDATED.value == "template_updated"
        assert AuditAction.TEMPLATE_DELETED.value == "template_deleted"
        assert AuditAction.VERSION_ACTIVATED.value == "version_activated"
        assert AuditAction.MODEL_UPDATED.value == "model_updated"
        assert AuditAction.TEMPLATE_TESTED.value == "template_tested"


@pytest.mark.unit
class TestLogTemplateCreated:
    """Test log_template_created method."""

    @pytest.fixture
    def service(self):
        """Create audit log service."""
        return AuditLogService()

    async def test_log_template_created_basic(self, service):
        """Test logging template creation with basic info."""
        # Act
        await service.log_template_created(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="1.0.0",
        )

        # Assert - should not raise

    async def test_log_template_created_with_source_version(self, service):
        """Test logging template creation with source version."""
        # Act
        await service.log_template_created(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="2.0.0",
            source_version="1.0.0",
        )

        # Assert - should not raise

    async def test_log_template_created_with_ip_address(self, service):
        """Test logging template creation with IP address."""
        # Act
        await service.log_template_created(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="1.0.0",
            ip_address="10.0.0.1",
        )

        # Assert - should not raise


@pytest.mark.unit
class TestLogTemplateUpdated:
    """Test log_template_updated method."""

    @pytest.fixture
    def service(self):
        """Create audit log service."""
        return AuditLogService()

    async def test_log_template_updated_basic(self, service):
        """Test logging template update with basic info."""
        # Arrange
        changes = {"system_prompt": "updated"}

        # Act
        await service.log_template_updated(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="1.0.0",
            changes=changes,
        )

        # Assert - should not raise

    async def test_log_template_updated_with_reason(self, service):
        """Test logging template update with reason."""
        # Arrange
        changes = {"system_prompt": "updated", "model": "changed"}

        # Act
        await service.log_template_updated(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="1.0.0",
            changes=changes,
            reason="Improved prompt clarity",
        )

        # Assert - should not raise

    async def test_log_template_updated_with_ip_address(self, service):
        """Test logging template update with IP address."""
        # Arrange
        changes = {"model": "updated"}

        # Act
        await service.log_template_updated(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="1.0.0",
            changes=changes,
            ip_address="10.0.0.1",
        )

        # Assert - should not raise


@pytest.mark.unit
class TestLogTemplateDeleted:
    """Test log_template_deleted method."""

    @pytest.fixture
    def service(self):
        """Create audit log service."""
        return AuditLogService()

    async def test_log_template_deleted_basic(self, service):
        """Test logging template deletion with basic info."""
        # Act
        await service.log_template_deleted(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="0.9.0",
        )

        # Assert - should not raise

    async def test_log_template_deleted_with_reason(self, service):
        """Test logging template deletion with reason."""
        # Act
        await service.log_template_deleted(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="0.9.0",
            reason="Obsolete version",
        )

        # Assert - should not raise


@pytest.mark.unit
class TestLogVersionActivated:
    """Test log_version_activated method."""

    @pytest.fixture
    def service(self):
        """Create audit log service."""
        return AuditLogService()

    async def test_log_version_activated_basic(self, service):
        """Test logging version activation with basic info."""
        # Act
        await service.log_version_activated(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            new_version="2.0.0",
        )

        # Assert - should not raise

    async def test_log_version_activated_with_previous_version(self, service):
        """Test logging version activation with previous version."""
        # Act
        await service.log_version_activated(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            new_version="2.0.0",
            previous_version="1.0.0",
        )

        # Assert - should not raise

    async def test_log_version_activated_with_reason(self, service):
        """Test logging version activation with reason."""
        # Act
        await service.log_version_activated(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            new_version="2.0.0",
            previous_version="1.0.0",
            reason="Completed testing",
        )

        # Assert - should not raise


@pytest.mark.unit
class TestLogModelUpdated:
    """Test log_model_updated method."""

    @pytest.fixture
    def service(self):
        """Create audit log service."""
        return AuditLogService()

    async def test_log_model_updated_basic(self, service):
        """Test logging model update with basic info."""
        # Arrange
        changes = {"is_active": "true"}

        # Act
        await service.log_model_updated(
            user_id="admin-123",
            tenant_id="tenant-456",
            model_id="anthropic.claude-3-5-sonnet",
            changes=changes,
        )

        # Assert - should not raise

    async def test_log_model_updated_with_reason(self, service):
        """Test logging model update with reason."""
        # Arrange
        changes = {"cost_per_1k_tokens": {"input": 0.003, "output": 0.015}}

        # Act
        await service.log_model_updated(
            user_id="admin-123",
            tenant_id="tenant-456",
            model_id="anthropic.claude-3-5-sonnet",
            changes=changes,
            reason="Updated pricing",
        )

        # Assert - should not raise


@pytest.mark.unit
class TestLogTemplateTested:
    """Test log_template_tested method."""

    @pytest.fixture
    def service(self):
        """Create audit log service."""
        return AuditLogService()

    async def test_log_template_tested_success(self, service):
        """Test logging successful template test."""
        # Arrange
        test_parameters = {"goal": "Test goal", "purpose": "Test purpose"}

        # Act
        await service.log_template_tested(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="2.0.0",
            test_parameters=test_parameters,
            success=True,
        )

        # Assert - should not raise

    async def test_log_template_tested_failure(self, service):
        """Test logging failed template test."""
        # Arrange
        test_parameters = {"goal": "Test goal"}

        # Act
        await service.log_template_tested(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="2.0.0",
            test_parameters=test_parameters,
            success=False,
        )

        # Assert - should not raise

    async def test_log_template_tested_with_ip_address(self, service):
        """Test logging template test with IP address."""
        # Arrange
        test_parameters = {"goal": "Test goal"}

        # Act
        await service.log_template_tested(
            user_id="admin-123",
            tenant_id="tenant-456",
            topic="goal_alignment",
            version="2.0.0",
            test_parameters=test_parameters,
            success=True,
            ip_address="10.0.0.1",
        )

        # Assert - should not raise
