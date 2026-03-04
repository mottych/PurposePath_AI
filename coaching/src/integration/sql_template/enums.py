"""Canonical enums for SQL template generation contract."""

from __future__ import annotations

from enum import StrEnum


class Provider(StrEnum):
    """Supported integration provider."""

    CDATA = "cdata"


class GenerationStatus(StrEnum):
    """Terminal generation status values."""

    SUCCESS = "success"
    FAILED = "failed"


class ErrorCode(StrEnum):
    """Stable terminal error codes."""

    SQL_POLICY_VIOLATION = "SQL_POLICY_VIOLATION"
    SQL_VALIDATION_FAILED = "SQL_VALIDATION_FAILED"
    SCHEMA_DISCOVERY_FAILED = "SCHEMA_DISCOVERY_FAILED"
    MCP_TOOL_ERROR = "MCP_TOOL_ERROR"
    AI_OUTPUT_INVALID = "AI_OUTPUT_INVALID"
    CDATA_AUTH_INVALID = "CDATA_AUTH_INVALID"
    CDATA_CONNECTION_NOT_FOUND = "CDATA_CONNECTION_NOT_FOUND"
    CDATA_RATE_LIMITED = "CDATA_RATE_LIMITED"
    INTERNAL_UNHANDLED = "INTERNAL_UNHANDLED"


class ErrorStage(StrEnum):
    """Pipeline stage where failure occurred."""

    DISCOVER = "DISCOVER"
    GENERATE = "GENERATE"
    VALIDATE = "VALIDATE"
    REPAIR = "REPAIR"
    PUBLISH = "PUBLISH"


class IgnoredParameterReason(StrEnum):
    """Canonical reason when a configured parameter is not used."""

    NOT_NEEDED_FOR_QUERY_SHAPE = "NOT_NEEDED_FOR_QUERY_SHAPE"
    UNSUPPORTED_BY_SOURCE_SCHEMA = "UNSUPPORTED_BY_SOURCE_SCHEMA"
    INVALID_OPERATOR_FOR_PARAMETER = "INVALID_OPERATOR_FOR_PARAMETER"
    NULL_NOT_ALLOWED = "NULL_NOT_ALLOWED"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    OUT_OF_POLICY = "OUT_OF_POLICY"


class ValidationFailureCode(StrEnum):
    """Canonical validation failure codes."""

    FORBIDDEN_TOKEN = "FORBIDDEN_TOKEN"
    UNBOUND_PARAMETER = "UNBOUND_PARAMETER"
    PLACEHOLDER_STYLE_MISMATCH = "PLACEHOLDER_STYLE_MISMATCH"
    MAX_ROWS_EXCEEDED = "MAX_ROWS_EXCEEDED"
    NON_DETERMINISTIC_RESULT_SHAPE = "NON_DETERMINISTIC_RESULT_SHAPE"
    SYNTAX_INVALID = "SYNTAX_INVALID"
    SCHEMA_OBJECT_NOT_FOUND = "SCHEMA_OBJECT_NOT_FOUND"


class ValidationMethod(StrEnum):
    """SQL validation method."""

    DRY_RUN = "dryRun"
    PROBE = "probe"
    QUERY_DATA = "queryData"


class AllowedOperator(StrEnum):
    """Supported filter operators for runtime parameters."""

    EQUALS = "EQUALS"
    IN = "IN"
