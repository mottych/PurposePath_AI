"""Event contracts and internal models for SQL template generation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from coaching.src.integration.sql_template.enums import (
    AllowedOperator,
    ErrorCode,
    ErrorStage,
    IgnoredParameterReason,
    Provider,
    ValidationFailureCode,
    ValidationMethod,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base class enforcing strict payload contracts."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DefinitionIdentity(StrictModel):
    version: int = Field(ge=1)
    hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class SystemContext(StrictModel):
    connection_id: UUID = Field(alias="connectionId")
    cdata_connection_id: str = Field(alias="cdataConnectionId", min_length=1)
    workspace: str = Field(default="default", min_length=1)


class IntentContext(StrictModel):
    time_zone: str = Field(alias="timeZone", min_length=1)
    date_field_semantics: str = Field(alias="dateFieldSemantics", min_length=1)


class IntentModel(StrictModel):
    template_definition: str = Field(alias="templateDefinition", min_length=1)
    resolved_period_window_strategy: str = Field(alias="resolvedPeriodWindowStrategy", min_length=1)
    resolved_context: IntentContext = Field(alias="resolvedContext")


class AllowedParameter(StrictModel):
    name: str = Field(min_length=1)
    data_type: str = Field(alias="dataType", min_length=1)
    required: bool
    nullable: bool
    operator_allowed: list[AllowedOperator] = Field(alias="operatorAllowed", min_length=1)


class ParameterValue(StrictModel):
    name: str = Field(min_length=1)
    operator: AllowedOperator
    value_type: str = Field(alias="valueType", min_length=1)
    value: str | float | int | bool | list[str] | list[float] | list[int]


class ParameterModel(StrictModel):
    allowed: list[AllowedParameter]
    values: list[ParameterValue]


class GenerationControl(StrictModel):
    regeneration_required: bool = Field(alias="regenerationRequired")


class SqlPolicy(StrictModel):
    dialect: str
    bind_placeholder_style: Literal["@name"] = Field(alias="bindPlaceholderStyle")
    must_use_parameterized_template: bool = Field(alias="mustUseParameterizedTemplate")
    forbidden: list[str] = Field(min_length=1)
    max_rows: int = Field(alias="maxRows", ge=1)
    max_rows_semantics: Literal["FINAL_RESULT_SET_ROWS"] = Field(alias="maxRowsSemantics")


class RequestedDetail(StrictModel):
    event_version: Literal["1.2"] = Field(alias="eventVersion")
    provider: Provider
    correlation_id: UUID = Field(alias="correlationId")
    generation_id: UUID = Field(alias="generationId")
    tenant_id: UUID = Field(alias="tenantId")
    measure_integration_id: UUID = Field(alias="measureIntegrationId")
    idempotency_key: str = Field(alias="idempotencyKey", min_length=1)
    catalog_measure_id: UUID = Field(alias="catalogMeasureId")
    measure_id: UUID = Field(alias="measureId")
    definition: DefinitionIdentity
    system: SystemContext
    intent: IntentModel
    parameter_model: ParameterModel = Field(alias="parameterModel")
    generation_control: GenerationControl = Field(alias="generationControl")
    sql_policy: SqlPolicy = Field(alias="sqlPolicy")
    runtime_bindings_expected: list[str] = Field(alias="runtimeBindingsExpected", min_length=1)


class RequestedEvent(StrictModel):
    version: str
    id: UUID
    detail_type: Literal["integration.sql.template.generate.requested"] = Field(alias="detail-type")
    source: Literal["purposepath.integration"]
    time: datetime
    account: str | None = None
    region: str | None = None
    resources: list[str] = Field(default_factory=list)
    detail: RequestedDetail


class IgnoredParameter(StrictModel):
    name: str
    reason: IgnoredParameterReason


class ValidationResult(StrictModel):
    method: ValidationMethod
    attempt_count: int = Field(alias="attemptCount", ge=1)


class GenerationMetadata(StrictModel):
    duration_ms: int = Field(alias="durationMs", ge=0)
    tool_calls: int = Field(alias="toolCalls", ge=0)


class CompletedDetail(StrictModel):
    event_version: Literal["1.2"] = Field(alias="eventVersion")
    provider: Provider
    correlation_id: UUID = Field(alias="correlationId")
    generation_id: UUID = Field(alias="generationId")
    tenant_id: UUID = Field(alias="tenantId")
    measure_integration_id: UUID = Field(alias="measureIntegrationId")
    idempotency_key: str = Field(alias="idempotencyKey")
    catalog_measure_id: UUID = Field(alias="catalogMeasureId")
    measure_id: UUID = Field(alias="measureId")
    definition: DefinitionIdentity
    system: SystemContext
    status: Literal["success"]
    sql_template: str = Field(alias="sqlTemplate", min_length=1)
    sql_template_hash: str = Field(alias="sqlTemplateHash", pattern=r"^sha256:[a-f0-9]{64}$")
    parameter_bindings_schema: dict[str, str] = Field(alias="parameterBindingsSchema")
    applied_parameters: list[str] = Field(alias="appliedParameters")
    ignored_parameters: list[IgnoredParameter] = Field(alias="ignoredParameters")
    validated: Literal[True]
    validation: ValidationResult
    generation_metadata: GenerationMetadata = Field(alias="generationMetadata")


class CompletedEvent(StrictModel):
    version: str = "0"
    id: UUID
    detail_type: Literal["integration.sql.template.generate.completed"] = Field(
        default="integration.sql.template.generate.completed",
        alias="detail-type",
    )
    source: Literal["purposepath.integration.ai"] = "purposepath.integration.ai"
    time: datetime
    account: str | None = None
    region: str | None = None
    resources: list[str] = Field(default_factory=list)
    detail: CompletedDetail


class ValidationFailure(StrictModel):
    code: ValidationFailureCode
    message: str


class FailedDetail(StrictModel):
    event_version: Literal["1.2"] = Field(alias="eventVersion")
    provider: Provider
    correlation_id: UUID = Field(alias="correlationId")
    generation_id: UUID = Field(alias="generationId")
    tenant_id: UUID = Field(alias="tenantId")
    measure_integration_id: UUID = Field(alias="measureIntegrationId")
    idempotency_key: str = Field(alias="idempotencyKey")
    catalog_measure_id: UUID = Field(alias="catalogMeasureId")
    measure_id: UUID = Field(alias="measureId")
    definition: DefinitionIdentity
    system: SystemContext
    status: Literal["failed"]
    error_code: ErrorCode = Field(alias="errorCode")
    error_stage: ErrorStage = Field(alias="errorStage")
    retryable: bool
    retry_after_seconds: int | None = Field(default=None, alias="retryAfterSeconds")
    message: str = Field(min_length=1)
    duration_ms: int = Field(alias="durationMs", ge=0)
    attempt_count: int = Field(alias="attemptCount", ge=1)
    cdata_error_code: str | None = Field(default=None, alias="cdataErrorCode")
    validation_failures: list[ValidationFailure] = Field(
        default_factory=list, alias="validationFailures"
    )


class FailedEvent(StrictModel):
    version: str = "0"
    id: UUID
    detail_type: Literal["integration.sql.template.generate.failed"] = Field(
        default="integration.sql.template.generate.failed",
        alias="detail-type",
    )
    source: Literal["purposepath.integration.ai"] = "purposepath.integration.ai"
    time: datetime
    account: str | None = None
    region: str | None = None
    resources: list[str] = Field(default_factory=list)
    detail: FailedDetail


class DiscoveredColumn(StrictModel):
    table_name: str
    column_name: str


class SqlGenerationResult(StrictModel):
    sql_template: str
    parameter_bindings_schema: dict[str, str]
    applied_parameters: list[str]
    ignored_parameters: list[IgnoredParameter]
    validation_method: ValidationMethod = ValidationMethod.DRY_RUN
    validation_attempt_count: int = 1
    tool_calls: int = 0

    @property
    def sql_template_hash(self) -> str:
        import hashlib

        digest = hashlib.sha256(self.sql_template.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


class GenerationRecord(StrictModel):
    generation_id: str
    status: Literal["PROCESSING", "COMPLETED", "FAILED"]
    terminal_payload: dict[str, object] | None = None
    terminal_detail_type: str | None = None
    published: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("generation_id")
    @classmethod
    def validate_generation_id(cls, value: str) -> str:
        UUID(value)
        return value
