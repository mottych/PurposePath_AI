"""DynamoDB repository for AI jobs.

This module provides a DynamoDB-backed repository for storing and
retrieving async AI job records.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from boto3.dynamodb.conditions import Key
from coaching.src.domain.entities.ai_job import AIJob, AIJobErrorCode, AIJobStatus, AIJobType

logger = structlog.get_logger()


class DynamoDBJobRepository:
    """DynamoDB repository for AI job persistence.

    This repository handles storing and retrieving AI job records
    in DynamoDB, with support for TTL-based auto-cleanup.

    Table Schema:
        - PK: job_id (String)
        - GSI: tenant_user_index (tenant_id, created_at)
        - TTL: ttl (Number - Unix timestamp)

    Design:
        - Jobs are stored with 24-hour TTL for automatic cleanup
        - GSI enables listing jobs by tenant/user
        - All timestamps stored as ISO 8601 strings
    """

    def __init__(
        self,
        dynamodb_resource: Any,  # boto3.resources.base.ServiceResource
        table_name: str,
    ) -> None:
        """Initialize DynamoDB job repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name for AI jobs
        """
        self.dynamodb = dynamodb_resource
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name
        logger.info("DynamoDB job repository initialized", table_name=table_name)

    async def save(self, job: AIJob) -> None:
        """Persist an AI job to DynamoDB.

        Args:
            job: AIJob entity to persist
        """
        try:
            item = self._to_dynamodb_item(job)
            self.table.put_item(Item=item)

            logger.info(
                "ai_job.saved",
                job_id=job.job_id,
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                status=job.status.value,
            )
        except Exception as e:
            logger.error(
                "ai_job.save_failed",
                job_id=job.job_id,
                error=str(e),
            )
            raise

    async def get_by_id(self, job_id: str) -> AIJob | None:
        """Retrieve an AI job by ID.

        Args:
            job_id: Unique job identifier

        Returns:
            AIJob if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"job_id": job_id})

            if "Item" not in response:
                logger.debug("ai_job.not_found", job_id=job_id)
                return None

            job = self._from_dynamodb_item(response["Item"])
            logger.debug("ai_job.retrieved", job_id=job_id, status=job.status.value)
            return job

        except Exception as e:
            logger.error(
                "ai_job.get_failed",
                job_id=job_id,
                error=str(e),
            )
            raise

    async def get_by_id_for_tenant(
        self,
        job_id: str,
        tenant_id: str,
    ) -> AIJob | None:
        """Retrieve an AI job by ID with tenant isolation.

        Args:
            job_id: Unique job identifier
            tenant_id: Tenant ID for isolation

        Returns:
            AIJob if found and belongs to tenant, None otherwise
        """
        job = await self.get_by_id(job_id)

        if job is None:
            return None

        # Enforce tenant isolation
        if job.tenant_id != tenant_id:
            logger.warning(
                "ai_job.tenant_isolation_violation",
                job_id=job_id,
                requested_tenant=tenant_id,
                actual_tenant=job.tenant_id,
            )
            return None

        return job

    async def update_status(
        self,
        job_id: str,
        status: AIJobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        error_code: AIJobErrorCode | None = None,
        processing_time_ms: int | None = None,
    ) -> bool:
        """Update job status atomically.

        Args:
            job_id: Job identifier
            status: New status
            result: Result data (for completed)
            error: Error message (for failed)
            error_code: Error code (for failed)
            processing_time_ms: Processing time (for terminal states)

        Returns:
            True if update succeeded, False if job not found
        """
        try:
            update_expr_parts = ["#status = :status"]
            expr_attr_names = {"#status": "status"}
            expr_attr_values: dict[str, Any] = {":status": status.value}

            now = datetime.now(UTC).isoformat()

            if status == AIJobStatus.PROCESSING:
                update_expr_parts.append("started_at = :started_at")
                expr_attr_values[":started_at"] = now

            if status in (AIJobStatus.COMPLETED, AIJobStatus.FAILED):
                update_expr_parts.append("completed_at = :completed_at")
                expr_attr_values[":completed_at"] = now

            if result is not None:
                update_expr_parts.append("#result = :result")
                expr_attr_names["#result"] = "result"
                expr_attr_values[":result"] = result

            if error is not None:
                update_expr_parts.append("#error = :error")
                expr_attr_names["#error"] = "error"
                expr_attr_values[":error"] = error

            if error_code is not None:
                update_expr_parts.append("error_code = :error_code")
                expr_attr_values[":error_code"] = error_code.value

            if processing_time_ms is not None:
                update_expr_parts.append("processing_time_ms = :processing_time_ms")
                expr_attr_values[":processing_time_ms"] = processing_time_ms

            update_expr = "SET " + ", ".join(update_expr_parts)

            self.table.update_item(
                Key={"job_id": job_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ConditionExpression="attribute_exists(job_id)",
            )

            logger.info(
                "ai_job.status_updated",
                job_id=job_id,
                status=status.value,
            )
            return True

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            logger.warning("ai_job.update_not_found", job_id=job_id)
            return False
        except Exception as e:
            logger.error(
                "ai_job.update_failed",
                job_id=job_id,
                error=str(e),
            )
            raise

    async def list_by_tenant_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 10,
    ) -> list[AIJob]:
        """List recent jobs for a tenant/user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            limit: Maximum number of jobs to return

        Returns:
            List of AIJob entities, most recent first
        """
        try:
            # Query GSI for tenant+user jobs
            # Note: Requires GSI on (tenant_id, created_at) with user_id filter
            response = self.table.query(
                IndexName="tenant-user-index",
                KeyConditionExpression=Key("tenant_id").eq(tenant_id),
                FilterExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit,
            )

            jobs = [self._from_dynamodb_item(item) for item in response.get("Items", [])]
            logger.debug(
                "ai_job.list_retrieved",
                tenant_id=tenant_id,
                user_id=user_id,
                count=len(jobs),
            )
            return jobs

        except Exception as e:
            logger.error(
                "ai_job.list_failed",
                tenant_id=tenant_id,
                user_id=user_id,
                error=str(e),
            )
            raise

    def _to_dynamodb_item(self, job: AIJob) -> dict[str, Any]:
        """Convert AIJob entity to DynamoDB item.

        Args:
            job: AIJob entity

        Returns:
            DynamoDB item dict
        """
        item: dict[str, Any] = {
            "job_id": job.job_id,
            "job_type": job.job_type.value,
            "tenant_id": job.tenant_id,
            "user_id": job.user_id,
            "topic_id": job.topic_id,
            "parameters": job.parameters,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "estimated_duration_ms": job.estimated_duration_ms,
        }

        # Optional fields for conversation_message jobs
        if job.session_id is not None:
            item["session_id"] = job.session_id

        if job.user_message is not None:
            item["user_message"] = job.user_message

        # Store JWT token for parameter enrichment during execution
        # Note: DynamoDB has encryption at rest, but token should be short-lived
        if job.jwt_token is not None:
            item["jwt_token"] = job.jwt_token

        if job.result is not None:
            item["result"] = job.result

        if job.error is not None:
            item["error"] = job.error

        if job.error_code is not None:
            item["error_code"] = job.error_code.value

        if job.started_at is not None:
            item["started_at"] = job.started_at.isoformat()

        if job.completed_at is not None:
            item["completed_at"] = job.completed_at.isoformat()

        if job.processing_time_ms is not None:
            item["processing_time_ms"] = job.processing_time_ms

        if job.ttl is not None:
            item["ttl"] = job.ttl

        return item

    def _from_dynamodb_item(self, item: dict[str, Any]) -> AIJob:
        """Convert DynamoDB item to AIJob entity.

        Args:
            item: DynamoDB item dict

        Returns:
            AIJob entity
        """
        return AIJob(
            job_id=item["job_id"],
            job_type=AIJobType(item.get("job_type", "single_shot")),
            tenant_id=item["tenant_id"],
            user_id=item["user_id"],
            topic_id=item["topic_id"],
            session_id=item.get("session_id"),
            user_message=item.get("user_message"),
            parameters=item.get("parameters", {}),
            jwt_token=item.get("jwt_token"),  # Retrieve token for enrichment
            status=AIJobStatus(item["status"]),
            result=item.get("result"),
            error=item.get("error"),
            error_code=AIJobErrorCode(item["error_code"]) if item.get("error_code") else None,
            created_at=datetime.fromisoformat(item["created_at"]),
            started_at=(
                datetime.fromisoformat(item["started_at"]) if item.get("started_at") else None
            ),
            completed_at=(
                datetime.fromisoformat(item["completed_at"]) if item.get("completed_at") else None
            ),
            estimated_duration_ms=item.get("estimated_duration_ms", 30000),
            processing_time_ms=item.get("processing_time_ms"),
            ttl=item.get("ttl"),
        )
