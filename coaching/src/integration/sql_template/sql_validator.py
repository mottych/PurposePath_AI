"""SQL policy and contract validator for generated templates."""

from __future__ import annotations

import re

from coaching.src.integration.sql_template.enums import ValidationFailureCode
from coaching.src.integration.sql_template.errors import PolicyViolationError, ValidationError
from coaching.src.integration.sql_template.models import RequestedDetail, SqlGenerationResult


class SqlTemplateValidator:
    """Validates generated SQL against policy and request compatibility rules."""

    PLACEHOLDER_PATTERN = re.compile(r"[@:][A-Za-z_][A-Za-z0-9_]*")

    def validate(self, request: RequestedDetail, generation: SqlGenerationResult) -> None:
        sql_upper = generation.sql_template.upper()

        for forbidden in request.sql_policy.forbidden:
            token = forbidden.upper()
            if re.search(rf"\b{re.escape(token)}\b", sql_upper):
                raise PolicyViolationError(
                    message=f"Generated SQL contains forbidden token: {token}",
                    validation_code=ValidationFailureCode.FORBIDDEN_TOKEN,
                )

        if request.sql_policy.must_use_parameterized_template:
            matched_placeholders = self.PLACEHOLDER_PATTERN.findall(generation.sql_template)
            if not matched_placeholders:
                raise ValidationError(
                    message="Generated SQL has no bind placeholders.",
                    validation_code=ValidationFailureCode.UNBOUND_PARAMETER,
                )

            expected_prefix = request.sql_policy.bind_placeholder_style[0]
            if any(
                not placeholder.startswith(expected_prefix) for placeholder in matched_placeholders
            ):
                raise ValidationError(
                    message="Generated SQL placeholder style does not match policy.",
                    validation_code=ValidationFailureCode.PLACEHOLDER_STYLE_MISMATCH,
                )

        binding_keys = set(generation.parameter_bindings_schema.keys())
        placeholder_bindings = {
            placeholder[1:]
            for placeholder in self.PLACEHOLDER_PATTERN.findall(generation.sql_template)
            if placeholder.startswith("@")
        }
        if not placeholder_bindings.issubset(binding_keys):
            raise ValidationError(
                message="Generated SQL includes placeholders without binding schema.",
                validation_code=ValidationFailureCode.UNBOUND_PARAMETER,
            )

        if "GROUP BY" in sql_upper and request.sql_policy.max_rows == 1:
            raise ValidationError(
                message="Generated SQL violates maxRows policy.",
                validation_code=ValidationFailureCode.MAX_ROWS_EXCEEDED,
            )

        if "SUM(" not in sql_upper and request.sql_policy.max_rows == 1:
            raise ValidationError(
                message="Generated SQL does not guarantee deterministic single-row shape.",
                validation_code=ValidationFailureCode.NON_DETERMINISTIC_RESULT_SHAPE,
            )

        expected_runtime_bindings = set(request.runtime_bindings_expected)
        if not expected_runtime_bindings.issubset(binding_keys):
            raise ValidationError(
                message="Generated bindings do not satisfy required runtime bindings.",
                validation_code=ValidationFailureCode.UNBOUND_PARAMETER,
            )
