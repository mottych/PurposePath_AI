"""DynamoDB repository for per-call LLM usage rows."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import structlog
from boto3.dynamodb.conditions import Attr, Key
from coaching.src.domain.entities.llm_usage_record import LlmUsageRecord

logger = structlog.get_logger()

_GSI_NAME = "billing-tenant-time-index"
_RETENTION_DAYS = 90


def _iso_z(dt: datetime) -> str:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_iso_z(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.fromisoformat(value)


class DynamoDBLlmUsageRepository:
    """PK tenant+billing month; GSI billing period for admin scans."""

    def __init__(
        self,
        dynamodb_resource: Any,
        table_name: str,
    ) -> None:
        self._table = dynamodb_resource.Table(table_name)
        self._table_name = table_name

    def _to_item(self, record: LlmUsageRecord) -> dict[str, Any]:
        occurred = _iso_z(record.occurred_at)
        pk = f"TENANT#{record.tenant_id}#BP#{record.billing_period}"
        sk = f"{occurred}#{record.usage_id}"
        gsi1_pk = f"BP#{record.billing_period}"
        gsi1_sk = f"{record.tenant_id}#{occurred}#{record.usage_id}"
        occurred_aware = (
            record.occurred_at.astimezone(UTC)
            if record.occurred_at.tzinfo
            else record.occurred_at.replace(tzinfo=UTC)
        )
        ttl_ts = int((occurred_aware + timedelta(days=_RETENTION_DAYS)).timestamp())
        item: dict[str, Any] = {
            "pk": pk,
            "sk": sk,
            "gsi1_pk": gsi1_pk,
            "gsi1_sk": gsi1_sk,
            "usage_id": record.usage_id,
            "occurred_at": occurred,
            "billing_period": record.billing_period,
            "tenant_id": record.tenant_id,
            "topic_id": record.topic_id,
            "topic_category": record.topic_category,
            "topic_type": record.topic_type,
            "model_code": record.model_code,
            "model_name": record.model_name,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "total_tokens": record.total_tokens,
            "max_tokens_topic_config": record.max_tokens_topic_config,
            "max_tokens_effective": record.max_tokens_effective,
            "wall_time_ms": record.wall_time_ms,
            "finish_reason": record.finish_reason,
            "entry_source": record.entry_source,
            "success": record.success,
            "ttl": ttl_ts,
        }
        if record.user_id is not None:
            item["user_id"] = record.user_id
        if record.estimated_duration_ms is not None:
            item["estimated_duration_ms"] = record.estimated_duration_ms
        if record.cost_usd is not None:
            item["cost_usd"] = Decimal(str(round(record.cost_usd, 6)))
        if record.job_id is not None:
            item["job_id"] = record.job_id
        if record.correlation_id is not None:
            item["correlation_id"] = record.correlation_id
        if record.session_id is not None:
            item["session_id"] = record.session_id
        if record.conversation_id is not None:
            item["conversation_id"] = record.conversation_id
        if record.error_kind is not None:
            item["error_kind"] = record.error_kind
        return item

    def _from_item(self, item: dict[str, Any]) -> LlmUsageRecord:
        cost_raw = item.get("cost_usd")
        cost: float | None
        if cost_raw is None:
            cost = None
        elif isinstance(cost_raw, Decimal):
            cost = float(cost_raw)
        else:
            cost = float(cost_raw)

        return LlmUsageRecord(
            usage_id=str(item["usage_id"]),
            occurred_at=_parse_iso_z(str(item["occurred_at"])),
            billing_period=str(item["billing_period"]),
            tenant_id=str(item["tenant_id"]),
            user_id=item.get("user_id"),
            topic_id=str(item["topic_id"]),
            topic_category=str(item["topic_category"]),
            topic_type=str(item["topic_type"]),
            model_code=str(item["model_code"]),
            model_name=str(item["model_name"]),
            input_tokens=int(item.get("input_tokens", 0)),
            output_tokens=int(item.get("output_tokens", 0)),
            total_tokens=int(item.get("total_tokens", 0)),
            max_tokens_topic_config=int(item["max_tokens_topic_config"]),
            max_tokens_effective=int(item["max_tokens_effective"]),
            wall_time_ms=int(item.get("wall_time_ms", 0)),
            estimated_duration_ms=item.get("estimated_duration_ms"),
            finish_reason=str(item.get("finish_reason", "")),
            cost_usd=cost,
            job_id=item.get("job_id"),
            correlation_id=item.get("correlation_id"),
            session_id=item.get("session_id"),
            conversation_id=item.get("conversation_id"),
            entry_source=item["entry_source"],
            success=bool(item.get("success", False)),
            error_kind=item.get("error_kind"),
        )

    async def append(self, record: LlmUsageRecord) -> None:
        self._table.put_item(Item=self._to_item(record))

    async def query_billing_period(
        self,
        *,
        billing_period: str,
        tenant_id_prefix: str | None,
        topic_id: str | None,
        model_substring: str | None,
        topic_category: str | None,
        topic_type: str | None,
        time_from: datetime | None,
        time_to: datetime | None,
        limit: int,
    ) -> list[LlmUsageRecord]:
        gsi1_pk = f"BP#{billing_period}"
        kwargs: dict[str, Any] = {
            "IndexName": _GSI_NAME,
            "KeyConditionExpression": Key("gsi1_pk").eq(gsi1_pk),
            "Limit": min(max(limit, 1), 2000),
        }
        if tenant_id_prefix:
            kwargs["KeyConditionExpression"] = Key("gsi1_pk").eq(gsi1_pk) & Key(
                "gsi1_sk"
            ).begins_with(f"{tenant_id_prefix}#")

        filter_parts: list[Any] = []
        if topic_id is not None:
            filter_parts.append(Attr("topic_id").eq(topic_id))
        if topic_category is not None:
            filter_parts.append(Attr("topic_category").eq(topic_category))
        if topic_type is not None:
            filter_parts.append(Attr("topic_type").eq(topic_type))
        if model_substring:
            filter_parts.append(Attr("model_name").contains(model_substring))

        fe: Any | None = None
        for p in filter_parts:
            fe = p if fe is None else fe & p
        if fe is not None:
            kwargs["FilterExpression"] = fe

        items: list[LlmUsageRecord] = []
        response = self._table.query(**kwargs)
        items.extend(self._from_item(i) for i in response.get("Items", []))

        def in_time_window(r: LlmUsageRecord) -> bool:
            return not (
                (time_from is not None and r.occurred_at < time_from.astimezone(UTC))
                or (time_to is not None and r.occurred_at > time_to.astimezone(UTC))
            )

        items = [r for r in items if in_time_window(r)]

        while "LastEvaluatedKey" in response and len(items) < limit:
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = self._table.query(**kwargs)
            batch = [self._from_item(i) for i in response.get("Items", [])]
            items.extend(r for r in batch if in_time_window(r))

        return items[:limit]

    async def query_topic_usage_across_periods(
        self,
        *,
        topic_id: str,
        billing_periods: list[str],
        time_from: datetime | None,
        time_to: datetime | None,
        max_items_total: int,
    ) -> list[LlmUsageRecord]:
        """Paginate GSI per month; filter by topic_id; cap total rows (admin topic stats)."""

        def in_time_window(r: LlmUsageRecord) -> bool:
            return not (
                (time_from is not None and r.occurred_at < time_from.astimezone(UTC))
                or (time_to is not None and r.occurred_at > time_to.astimezone(UTC))
            )

        cap = max(1, min(max_items_total, 100_000))
        out: list[LlmUsageRecord] = []
        for bp in billing_periods:
            if len(out) >= cap:
                break
            remaining = cap - len(out)
            page_out = self._query_gsi_month_topic_paginated(
                billing_period=bp,
                topic_id=topic_id,
                time_filter=in_time_window,
                max_items=remaining,
            )
            out.extend(page_out)
        return out

    def _query_gsi_month_topic_paginated(
        self,
        *,
        billing_period: str,
        topic_id: str,
        time_filter: Callable[[LlmUsageRecord], bool],
        max_items: int,
    ) -> list[LlmUsageRecord]:
        gsi1_pk = f"BP#{billing_period}"
        base_kwargs: dict[str, Any] = {
            "IndexName": _GSI_NAME,
            "KeyConditionExpression": Key("gsi1_pk").eq(gsi1_pk),
            "FilterExpression": Attr("topic_id").eq(topic_id),
        }
        collected: list[LlmUsageRecord] = []
        exclusive_key: dict[str, Any] | None = None
        while len(collected) < max_items:
            kwargs = {**base_kwargs, "Limit": 1000}
            if exclusive_key is not None:
                kwargs["ExclusiveStartKey"] = exclusive_key
            response = self._table.query(**kwargs)
            for raw in response.get("Items", []):
                rec = self._from_item(raw)
                if time_filter(rec):
                    collected.append(rec)
                    if len(collected) >= max_items:
                        break
            exclusive_key = response.get("LastEvaluatedKey")
            if not exclusive_key:
                break
        return collected
