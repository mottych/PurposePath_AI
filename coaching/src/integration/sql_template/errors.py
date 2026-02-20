"""SQL template generation exceptions and mapping helpers."""

from __future__ import annotations

from dataclasses import dataclass

from coaching.src.integration.sql_template.enums import ErrorCode, ErrorStage, ValidationFailureCode
from coaching.src.integration.sql_template.models import ValidationFailure


@dataclass(slots=True)
class SqlTemplateGenerationError(Exception):
    """Base typed exception for generation failures."""

    code: ErrorCode
    stage: ErrorStage
    message: str
    retryable: bool = False
    attempt_count: int = 1
    cdata_error_code: str | None = None
    validation_failures: list[ValidationFailure] | None = None

    def __str__(self) -> str:
        return self.message


class PolicyViolationError(SqlTemplateGenerationError):
    """Raised when SQL violates policy constraints."""

    def __init__(self, message: str, validation_code: ValidationFailureCode) -> None:
        super().__init__(
            code=ErrorCode.SQL_POLICY_VIOLATION,
            stage=ErrorStage.VALIDATE,
            message=message,
            retryable=False,
            validation_failures=[ValidationFailure(code=validation_code, message=message)],
        )


class ValidationError(SqlTemplateGenerationError):
    """Raised when SQL validation fails."""

    def __init__(self, message: str, validation_code: ValidationFailureCode) -> None:
        super().__init__(
            code=ErrorCode.SQL_VALIDATION_FAILED,
            stage=ErrorStage.VALIDATE,
            message=message,
            retryable=False,
            validation_failures=[ValidationFailure(code=validation_code, message=message)],
        )
