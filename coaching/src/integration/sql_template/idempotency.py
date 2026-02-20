"""Idempotency persistence for SQL template generation events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from botocore.exceptions import ClientError
from coaching.src.integration.sql_template.models import GenerationRecord


class GenerationIdempotencyStore(Protocol):
    """Port for generation idempotency state."""

    async def get(self, generation_id: str) -> GenerationRecord | None:
        """Fetch generation state by generation id."""

    async def reserve_processing(self, generation_id: str) -> bool:
        """Reserve a generation id for processing; returns False if already exists."""

    async def save_terminal(
        self,
        generation_id: str,
        status: str,
        detail_type: str,
        payload: dict[str, object],
    ) -> None:
        """Persist terminal state with payload snapshot."""

    async def mark_published(self, generation_id: str) -> None:
        """Mark terminal payload as published."""


class DynamoTableClient(Protocol):
    """Minimal DynamoDB table methods used by this store."""

    def get_item(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch an item."""

    def put_item(self, **kwargs: Any) -> dict[str, Any]:
        """Put an item."""

    def update_item(self, **kwargs: Any) -> dict[str, Any]:
        """Update an item."""


class DynamoGenerationIdempotencyStore:
    """DynamoDB-backed idempotency store."""

    def __init__(self, dynamodb_table: DynamoTableClient, ttl_hours: int = 48) -> None:
        self._table = dynamodb_table
        self._ttl_hours = ttl_hours

    async def get(self, generation_id: str) -> GenerationRecord | None:
        response = self._table.get_item(Key={"generation_id": generation_id})
        item = response.get("Item")
        if not item:
            return None
        return GenerationRecord.model_validate(item)

    async def reserve_processing(self, generation_id: str) -> bool:
        now = datetime.now(UTC)
        ttl = int((now + timedelta(hours=self._ttl_hours)).timestamp())
        try:
            self._table.put_item(
                Item={
                    "generation_id": generation_id,
                    "status": "PROCESSING",
                    "updated_at": now.isoformat(),
                    "published": False,
                    "ttl": ttl,
                },
                ConditionExpression="attribute_not_exists(generation_id)",
            )
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return False
            raise

    async def save_terminal(
        self,
        generation_id: str,
        status: str,
        detail_type: str,
        payload: dict[str, object],
    ) -> None:
        normalized_status = "COMPLETED" if status == "success" else "FAILED"
        now = datetime.now(UTC)
        self._table.update_item(
            Key={"generation_id": generation_id},
            UpdateExpression=(
                "SET #status = :status, terminal_detail_type = :detail_type, "
                "terminal_payload = :payload, published = :published, updated_at = :updated_at"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": normalized_status,
                ":detail_type": detail_type,
                ":payload": payload,
                ":published": False,
                ":updated_at": now.isoformat(),
            },
        )

    async def mark_published(self, generation_id: str) -> None:
        self._table.update_item(
            Key={"generation_id": generation_id},
            UpdateExpression="SET published = :published",
            ExpressionAttributeValues={":published": True},
        )


class InMemoryGenerationIdempotencyStore:
    """In-memory store for tests."""

    def __init__(self) -> None:
        self._records: dict[str, GenerationRecord] = {}

    async def get(self, generation_id: str) -> GenerationRecord | None:
        return self._records.get(generation_id)

    async def reserve_processing(self, generation_id: str) -> bool:
        if generation_id in self._records:
            return False
        self._records[generation_id] = GenerationRecord(
            generation_id=generation_id, status="PROCESSING"
        )
        return True

    async def save_terminal(
        self,
        generation_id: str,
        status: str,
        detail_type: str,
        payload: dict[str, object],
    ) -> None:
        self._records[generation_id] = GenerationRecord(
            generation_id=generation_id,
            status="COMPLETED" if status == "success" else "FAILED",
            terminal_detail_type=detail_type,
            terminal_payload=payload,
            published=False,
        )

    async def mark_published(self, generation_id: str) -> None:
        current = self._records[generation_id]
        self._records[generation_id] = GenerationRecord(
            generation_id=current.generation_id,
            status=current.status,
            terminal_detail_type=current.terminal_detail_type,
            terminal_payload=current.terminal_payload,
            published=True,
            updated_at=current.updated_at,
        )
