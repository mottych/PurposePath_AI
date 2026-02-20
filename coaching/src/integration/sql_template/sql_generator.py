"""SQL template generator for measure integration requests."""

from __future__ import annotations

import re
from collections import defaultdict

from coaching.src.integration.sql_template.enums import IgnoredParameterReason
from coaching.src.integration.sql_template.models import (
    DiscoveredColumn,
    IgnoredParameter,
    RequestedDetail,
    SqlGenerationResult,
)

DATE_COLUMN_HINTS = ("postdate", "orderdate", "createdat", "date", "timestamp")
VALUE_COLUMN_HINTS = ("totalamount", "amount", "revenue", "grossrevenue", "total")


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


class SqlTemplateGenerator:
    """Builds a deterministic parameterized SQL template from request + schema."""

    def generate(
        self,
        request: RequestedDetail,
        discovered_columns: list[DiscoveredColumn],
    ) -> SqlGenerationResult:
        by_table: dict[str, list[str]] = defaultdict(list)
        for item in discovered_columns:
            by_table[item.table_name].append(item.column_name)

        table_name, date_column, value_column = self._select_table_columns(by_table)
        alias = "m"
        where_clauses = [
            f"{alias}.{date_column} >= @startDate",
            f"{alias}.{date_column} < @endDate",
        ]

        bindings: dict[str, str] = {
            "startDate": "DateTime",
            "endDate": "DateTime",
        }
        applied: list[str] = []
        ignored: list[IgnoredParameter] = []

        allowed_by_name = {param.name: param for param in request.parameter_model.allowed}

        for configured_value in request.parameter_model.values:
            allowed_param = allowed_by_name.get(configured_value.name)
            if allowed_param is None:
                ignored.append(
                    IgnoredParameter(
                        name=configured_value.name,
                        reason=IgnoredParameterReason.OUT_OF_POLICY,
                    )
                )
                continue

            candidate_column = self._find_parameter_column(
                configured_value.name, by_table.get(table_name, [])
            )
            if candidate_column is None:
                ignored.append(
                    IgnoredParameter(
                        name=configured_value.name,
                        reason=IgnoredParameterReason.NOT_NEEDED_FOR_QUERY_SHAPE,
                    )
                )
                continue

            param_placeholder = f"@{configured_value.name}"
            if configured_value.operator.value == "EQUALS":
                where_clauses.append(
                    f"({param_placeholder} IS NULL OR {alias}.{candidate_column} = {param_placeholder})"
                )
                bindings[configured_value.name] = "String"
                applied.append(configured_value.name)
            elif configured_value.operator.value == "IN":
                where_clauses.append(
                    f"({param_placeholder} IS NULL OR {alias}.{candidate_column} IN ({param_placeholder}))"
                )
                bindings[configured_value.name] = "StringArray"
                applied.append(configured_value.name)
            else:
                ignored.append(
                    IgnoredParameter(
                        name=configured_value.name,
                        reason=IgnoredParameterReason.INVALID_OPERATOR_FOR_PARAMETER,
                    )
                )

        sql = (
            f"SELECT SUM({alias}.{value_column}) AS value FROM {table_name} {alias} "
            f"WHERE {' AND '.join(where_clauses)};"
        )
        return SqlGenerationResult(
            sql_template=sql,
            parameter_bindings_schema=bindings,
            applied_parameters=applied,
            ignored_parameters=ignored,
        )

    def _select_table_columns(
        self,
        by_table: dict[str, list[str]],
    ) -> tuple[str, str, str]:
        best_table = ""
        best_score = -1
        selected_date = ""
        selected_value = ""

        for table_name, columns in by_table.items():
            normalized = {column: _normalize(column) for column in columns}
            date_column = self._find_hint_match(normalized, DATE_COLUMN_HINTS)
            value_column = self._find_hint_match(normalized, VALUE_COLUMN_HINTS)
            score = 0
            if date_column:
                score += 1
            if value_column:
                score += 2
            if score > best_score:
                best_score = score
                best_table = table_name
                selected_date = date_column
                selected_value = value_column

        if not best_table:
            return "Records", "CreatedAt", "Amount"
        return (
            best_table,
            selected_date or "CreatedAt",
            selected_value or "Amount",
        )

    def _find_hint_match(self, normalized: dict[str, str], hints: tuple[str, ...]) -> str:
        for column, normalized_name in normalized.items():
            for hint in hints:
                if hint in normalized_name:
                    return column
        return ""

    def _find_parameter_column(self, parameter_name: str, columns: list[str]) -> str | None:
        normalized_param = _normalize(parameter_name)
        for column in columns:
            normalized_column = _normalize(column)
            if normalized_param in normalized_column or normalized_column in normalized_param:
                return column
        return None
