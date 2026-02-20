"""EventBridge publisher for SQL template generation terminal events."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import boto3
import structlog
from botocore.exceptions import ClientError
from pydantic import BaseModel

logger = structlog.get_logger()


class IntegrationEventPublisher:
    """Publishes pre-modeled terminal events to EventBridge."""

    def __init__(
        self,
        region_name: str,
        event_bus_name: str = "default",
    ) -> None:
        self._client: Any = boto3.client("events", region_name=region_name)
        self._bus_name = event_bus_name

    def publish_modeled_event(self, event_model: BaseModel, detail_type: str, source: str) -> str:
        detail = event_model.model_dump(mode="json", by_alias=True)
        entry = {
            "Source": source,
            "DetailType": detail_type,
            "Detail": json.dumps(detail),
            "EventBusName": self._bus_name,
            "Time": datetime.now(UTC),
        }
        logger.info(
            "integration_sql.eventbridge_publish_attempt",
            detail_type=detail_type,
            source=source,
        )
        try:
            response = self._client.put_events(Entries=[entry])
        except ClientError as exc:
            raise RuntimeError(f"EventBridge publish failed: {exc}") from exc

        if response.get("FailedEntryCount", 0) > 0:
            failed_entry = response.get("Entries", [{}])[0]
            raise RuntimeError(
                "EventBridge publish failed: "
                f"{failed_entry.get('ErrorCode')} - {failed_entry.get('ErrorMessage')}"
            )
        event_id = str(response.get("Entries", [{}])[0].get("EventId", ""))
        logger.info(
            "integration_sql.eventbridge_published", detail_type=detail_type, event_id=event_id
        )
        return event_id
