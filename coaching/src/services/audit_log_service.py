"""Audit logging service for tracking admin actions."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class AuditAction(str, Enum):
    """Types of auditable actions."""

    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    VERSION_ACTIVATED = "version_activated"
    MODEL_UPDATED = "model_updated"
    TEMPLATE_TESTED = "template_tested"


class AuditLogEntry(BaseModel):
    """Audit log entry model."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    action: AuditAction = Field(..., description="Action performed")
    user_id: str = Field(..., description="Admin user who performed the action")
    tenant_id: str = Field(..., description="Tenant context")
    resource_type: str = Field(..., description="Type of resource (e.g., 'template', 'model')")
    resource_id: str = Field(..., description="Identifier of the resource")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    ip_address: str | None = Field(None, description="IP address of the request")
    user_agent: str | None = Field(None, description="User agent of the request")


class AuditLogService:
    """Service for logging administrative actions for compliance and auditing."""

    def __init__(self) -> None:
        """Initialize audit log service."""
        logger.info("Audit log service initialized")

    async def log_template_created(
        self,
        user_id: str,
        tenant_id: str,
        topic: str,
        version: str,
        source_version: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log template creation event.

        Args:
            user_id: Admin user ID
            tenant_id: Tenant ID
            topic: Template topic
            version: New version identifier
            source_version: Source version if copied from existing
            ip_address: Request IP address
        """
        details: dict[str, Any] = {
            "topic": topic,
            "version": version,
        }
        if source_version:
            details["source_version"] = source_version

        entry = AuditLogEntry(
            action=AuditAction.TEMPLATE_CREATED,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="template",
            resource_id=f"{topic}/{version}",
            details=details,
            ip_address=ip_address,
            user_agent=None,
        )

        await self._write_log(entry)

    async def log_template_updated(
        self,
        user_id: str,
        tenant_id: str,
        topic: str,
        version: str,
        changes: dict[str, Any],
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log template update event.

        Args:
            user_id: Admin user ID
            tenant_id: Tenant ID
            topic: Template topic
            version: Version identifier
            changes: Dictionary of changed fields
            reason: Optional reason for the change
            ip_address: Request IP address
        """
        details: dict[str, Any] = {
            "topic": topic,
            "version": version,
            "changes": changes,
        }
        if reason:
            details["reason"] = reason

        entry = AuditLogEntry(
            action=AuditAction.TEMPLATE_UPDATED,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="template",
            resource_id=f"{topic}/{version}",
            details=details,
            ip_address=ip_address,
            user_agent=None,
        )

        await self._write_log(entry)

    async def log_template_deleted(
        self,
        user_id: str,
        tenant_id: str,
        topic: str,
        version: str,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log template deletion event.

        Args:
            user_id: Admin user ID
            tenant_id: Tenant ID
            topic: Template topic
            version: Version identifier
            reason: Optional reason for deletion
            ip_address: Request IP address
        """
        details: dict[str, Any] = {
            "topic": topic,
            "version": version,
        }
        if reason:
            details["reason"] = reason

        entry = AuditLogEntry(
            action=AuditAction.TEMPLATE_DELETED,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="template",
            resource_id=f"{topic}/{version}",
            details=details,
            ip_address=ip_address,
            user_agent=None,
        )

        await self._write_log(entry)

    async def log_version_activated(
        self,
        user_id: str,
        tenant_id: str,
        topic: str,
        new_version: str,
        previous_version: str | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log version activation event.

        Args:
            user_id: Admin user ID
            tenant_id: Tenant ID
            topic: Template topic
            new_version: Version being activated
            previous_version: Previous active version
            reason: Optional reason for activation
            ip_address: Request IP address
        """
        details: dict[str, Any] = {
            "topic": topic,
            "new_version": new_version,
        }
        if previous_version:
            details["previous_version"] = previous_version
        if reason:
            details["reason"] = reason

        entry = AuditLogEntry(
            action=AuditAction.VERSION_ACTIVATED,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="template",
            resource_id=f"{topic}/{new_version}",
            details=details,
            ip_address=ip_address,
            user_agent=None,
        )

        await self._write_log(entry)

    async def log_model_updated(
        self,
        user_id: str,
        tenant_id: str,
        model_id: str,
        changes: dict[str, Any],
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log model configuration update event.

        Args:
            user_id: Admin user ID
            tenant_id: Tenant ID
            model_id: Model identifier
            changes: Dictionary of changed fields
            reason: Optional reason for the change
            ip_address: Request IP address
        """
        details: dict[str, Any] = {
            "model_id": model_id,
            "changes": changes,
        }
        if reason:
            details["reason"] = reason

        entry = AuditLogEntry(
            action=AuditAction.MODEL_UPDATED,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="model",
            resource_id=model_id,
            details=details,
            ip_address=ip_address,
            user_agent=None,
        )

        await self._write_log(entry)

    async def log_template_tested(
        self,
        user_id: str,
        tenant_id: str,
        topic: str,
        version: str,
        test_parameters: dict[str, Any],
        success: bool,
        ip_address: str | None = None,
    ) -> None:
        """Log template testing event.

        Args:
            user_id: Admin user ID
            tenant_id: Tenant ID
            topic: Template topic
            version: Version tested
            test_parameters: Parameters used in test
            success: Whether test was successful
            ip_address: Request IP address
        """
        details: dict[str, Any] = {
            "topic": topic,
            "version": version,
            "test_parameters": test_parameters,
            "success": success,
        }

        entry = AuditLogEntry(
            action=AuditAction.TEMPLATE_TESTED,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="template",
            resource_id=f"{topic}/{version}",
            details=details,
            ip_address=ip_address,
            user_agent=None,
        )

        await self._write_log(entry)

    async def _write_log(self, entry: AuditLogEntry) -> None:
        """Write audit log entry to storage.

        In production, this would write to:
        - DynamoDB table for queryability
        - CloudWatch Logs for long-term retention
        - S3 for archival

        For now, we log to structured logger.

        Args:
            entry: Audit log entry to write
        """
        logger.info(
            "AUDIT_LOG",
            timestamp=entry.timestamp.isoformat(),
            action=entry.action.value,
            user_id=entry.user_id,
            tenant_id=entry.tenant_id,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            details=entry.details,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
        )

        # TODO: In production, also write to:
        # 1. DynamoDB audit table for querying
        # 2. S3 for long-term archival
        # 3. CloudWatch Logs with specific log group


__all__ = ["AuditAction", "AuditLogEntry", "AuditLogService"]
