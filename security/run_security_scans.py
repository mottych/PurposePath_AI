#!/usr/bin/env python3
"""Repository security scan orchestrator.

This script runs a deterministic set of security scanners and writes machine-readable
results to .artifacts/security.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SECURITY_DIR = REPO_ROOT / "security"
FINDINGS_DIR = REPO_ROOT / ".artifacts" / "security"

PYTHON = sys.executable


DETECT_SECRETS_EXCLUDE_REGEX = (
    r"(^|/)(\.venv|\.venv-security|venv|node_modules|__pycache__|\.pytest_cache|"
    r"\.mypy_cache|\.ruff_cache|docs|coaching/tests|tests|\.artifacts/security)(/|$)|"
    r"\.(md|txt|svg|png|jpg|jpeg|gif|webp|pdf)$"
)

AI_RISK_PATTERNS = [
    {
        "id": "AI001",
        "severity": "high",
        "pattern": re.compile(r"allow_dangerous_deserialization\s*=\s*True"),
        "message": "LangChain dangerous deserialization enabled",
        "source_references": [
            {"source": "CWE", "rule_id": "CWE-502"},
            {"source": "OWASP Top 10 2021", "rule_id": "A08:2021"},
        ],
    },
    {
        "id": "AI002",
        "severity": "high",
        "pattern": re.compile(r"\b(eval|exec)\s*\("),
        "message": "Dynamic code execution may execute model/user-controlled input",
        "source_references": [
            {"source": "CWE", "rule_id": "CWE-95"},
            {"source": "OWASP Top 10 2021", "rule_id": "A03:2021"},
        ],
    },
    {
        "id": "AI003",
        "severity": "medium",
        "pattern": re.compile(r"\b(pickle\.load|pickle\.loads|joblib\.load)\s*\("),
        "message": "Unsafe model/artifact deserialization detected",
        "source_references": [
            {"source": "CWE", "rule_id": "CWE-502"},
            {"source": "OWASP Top 10 2021", "rule_id": "A08:2021"},
        ],
    },
]

SCANNER_FRAMEWORK_MAPPINGS: dict[str, list[dict[str, str]]] = {
    "bandit": [
        {"source": "Bandit", "rule_id": "B***"},
        {"source": "OWASP Top 10 2021", "rule_id": "A03:2021"},
        {"source": "SOC 2 Trust Services Criteria", "rule_id": "CC7.1"},
        {"source": "AWS Well-Architected Security Pillar", "rule_id": "SEC03"},
    ],
    "pip-audit": [
        {"source": "PyPA Advisory Database", "rule_id": "PYSEC-*"},
        {"source": "GitHub Advisory Database", "rule_id": "GHSA-*"},
        {"source": "CVE", "rule_id": "CVE-*"},
        {"source": "OWASP Top 10 2021", "rule_id": "A06:2021"},
        {"source": "SOC 2 Trust Services Criteria", "rule_id": "CC8.1"},
        {"source": "AWS Well-Architected Security Pillar", "rule_id": "SEC05"},
    ],
    "checkov": [
        {"source": "Checkov", "rule_id": "CKV_* / CKV2_*"},
        {"source": "CIS Benchmarks", "rule_id": "control-specific"},
        {"source": "OWASP Top 10 2021", "rule_id": "A05:2021"},
        {"source": "SOC 2 Trust Services Criteria", "rule_id": "CC6.6"},
        {"source": "AWS Well-Architected Security Pillar", "rule_id": "SEC02"},
    ],
    "detect-secrets": [
        {"source": "detect-secrets", "rule_id": "plugin-type"},
        {"source": "OWASP Top 10 2021", "rule_id": "A02:2021"},
        {"source": "SOC 2 Trust Services Criteria", "rule_id": "CC6.1"},
        {"source": "AWS Well-Architected Security Pillar", "rule_id": "SEC08"},
    ],
    "ai-risk-checks": [
        {"source": "PurposePath AI Risk Rules", "rule_id": "AI001-AI003"},
        {"source": "OWASP Top 10 2021", "rule_id": "A03:2021 / A08:2021"},
        {"source": "SOC 2 Trust Services Criteria", "rule_id": "CC7.2"},
        {"source": "AWS Well-Architected Security Pillar", "rule_id": "SEC10"},
    ],
}

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

SEVERITY_TO_CHECKOV = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "info": "INFO",
}

CHECKOV_TO_SEVERITY = {value: key for key, value in SEVERITY_TO_CHECKOV.items()}


def normalize_severity(value: str | None) -> str:
    if not value:
        return "medium"
    normalized = str(value).strip().lower()
    if normalized in SEVERITY_ORDER:
        return normalized
    if normalized == "undefined":
        return "medium"
    return "medium"


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def source_refs_for(scanner: str, extra_rule_id: str | None = None) -> list[dict[str, str]]:
    refs = [dict(item) for item in SCANNER_FRAMEWORK_MAPPINGS.get(scanner, [])]
    if extra_rule_id and not any(item.get("rule_id") == extra_rule_id for item in refs):
        refs.insert(0, {"source": scanner, "rule_id": extra_rule_id})
    return refs


def bandit_remediation_for(test_id: str) -> tuple[str, str]:
    remediations = {
        "B104": (
            "Service may bind to all network interfaces.",
            "Bind services to explicit trusted interfaces where possible and enforce ingress controls.",
        ),
        "B105": (
            "Potential secret-like value is hardcoded in source.",
            "Move secrets to secure configuration/secret manager and replace literals with references.",
        ),
        "B112": (
            "Exception handling may suppress security-relevant failures.",
            "Replace bare continue handling with explicit exception handling and security-aware logging.",
        ),
        "B608": (
            "String-built SQL can enable injection paths.",
            "Use parameterized queries or query builders; avoid string concatenation in SQL statements.",
        ),
    }
    return remediations.get(
        test_id,
        (
            "Static analysis identified a potential secure coding issue.",
            "Review the code path and apply least-privilege, input validation, and secure coding controls.",
        ),
    )


def infer_dependency_severity(description: str) -> str:
    lower = description.lower()
    if "remote code execution" in lower or "arbitrary code execution" in lower:
        return "high"
    if "path traversal" in lower or "ssrf" in lower:
        return "high"
    if "denial of service" in lower or "redos" in lower:
        return "medium"
    return "medium"


def parse_bandit_findings() -> list[dict[str, Any]]:
    path = FINDINGS_DIR / "bandit.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        rule_id = str(item.get("test_id", "B???"))
        impact, remediation = bandit_remediation_for(rule_id)
        source_refs = source_refs_for("bandit", rule_id)
        findings.append(
            {
                "severity": normalize_severity(str(item.get("issue_severity", "MEDIUM"))),
                "scanner": "bandit",
                "title": str(item.get("issue_text", "Bandit finding")),
                "impact": impact,
                "remediation": remediation,
                "location": f"{item.get('filename', 'unknown')}:{item.get('line_number', '?')}",
                "rule_id": rule_id,
                "source_references": source_refs,
            }
        )
    return findings


def parse_pip_audit_findings() -> list[dict[str, Any]]:
    path = FINDINGS_DIR / "pip-audit.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings: list[dict[str, Any]] = []
    for dep in payload.get("dependencies", []):
        dep_name = str(dep.get("name", "unknown"))
        dep_version = str(dep.get("version", "unknown"))
        for vuln in dep.get("vulns", []):
            vuln_id = str(vuln.get("id", "advisory"))
            description = str(vuln.get("description", "Dependency vulnerability identified."))
            severity = infer_dependency_severity(description)
            fix_versions = vuln.get("fix_versions", [])
            remediation = (
                f"Upgrade `{dep_name}` from `{dep_version}` to a fixed version "
                f"({', '.join(fix_versions) if fix_versions else 'as recommended by advisory'})."
            )
            source_refs = source_refs_for("pip-audit", vuln_id)
            for alias in vuln.get("aliases", []):
                source_refs.append({"source": "Alias", "rule_id": str(alias)})
            findings.append(
                {
                    "severity": severity,
                    "scanner": "pip-audit",
                    "title": f"{dep_name} {dep_version}: {vuln_id}",
                    "impact": description[:280],
                    "remediation": remediation,
                    "location": f"dependency:{dep_name}",
                    "rule_id": vuln_id,
                    "source_references": source_refs,
                }
            )
    return findings


def parse_checkov_findings() -> list[dict[str, Any]]:
    path = FINDINGS_DIR / "checkov.json"
    if path.is_dir():
        path = path / "results_json.json"
    if not path.exists() or not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        checks = payload.get("results", {}).get("failed_checks", [])
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                checks.extend(item.get("results", {}).get("failed_checks", []))
    findings: list[dict[str, Any]] = []
    for check in checks:
        rule_id = str(check.get("check_id", "CKV_UNKNOWN"))
        check_name = str(check.get("check_name", "Checkov finding"))
        severity = CHECKOV_TO_SEVERITY.get(str(check.get("severity", "MEDIUM")).upper(), "medium")
        path_hint = str(check.get("file_path", "unknown"))
        impact = "Infrastructure or CI configuration may violate recommended security controls."
        remediation = (
            "Update the referenced infrastructure/workflow configuration to satisfy the Checkov control "
            "or document an approved risk acceptance."
        )
        source_refs = source_refs_for("checkov", rule_id)
        findings.append(
            {
                "severity": severity,
                "scanner": "checkov",
                "title": check_name,
                "impact": impact,
                "remediation": remediation,
                "location": path_hint,
                "rule_id": rule_id,
                "source_references": source_refs,
            }
        )
    return findings


def parse_detect_secrets_findings() -> list[dict[str, Any]]:
    path = FINDINGS_DIR / "detect-secrets.delta.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings: list[dict[str, Any]] = []
    for item in payload.get("new_findings", []):
        finding_type = str(item.get("type", "Secret finding"))
        source_refs = source_refs_for("detect-secrets", finding_type)
        findings.append(
            {
                "severity": "high",
                "scanner": "detect-secrets",
                "title": finding_type,
                "impact": "Potential credential/token exposure may allow unauthorized access or lateral movement.",
                "remediation": "Rotate exposed secrets, remove hardcoded values, and source runtime secrets from AWS Secrets Manager/SSM.",
                "location": str(item.get("file", "unknown")),
                "rule_id": finding_type,
                "source_references": source_refs,
            }
        )
    return findings


def parse_ai_risk_findings() -> list[dict[str, Any]]:
    path = FINDINGS_DIR / "ai-risk-checks.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings: list[dict[str, Any]] = []
    for item in payload.get("findings", []):
        source_refs = source_refs_for("ai-risk-checks", str(item.get("rule_id", "AI")))
        for extra in item.get("source_references", []):
            if isinstance(extra, dict) and "source" in extra and "rule_id" in extra:
                source_refs.append({"source": str(extra["source"]), "rule_id": str(extra["rule_id"])})
        findings.append(
            {
                "severity": normalize_severity(str(item.get("severity", "medium"))),
                "scanner": "ai-risk-checks",
                "title": str(item.get("message", "AI risk finding")),
                "impact": "Unsafe model-input/output handling can lead to data exposure or execution-path abuse.",
                "remediation": "Apply strict schema validation, avoid dangerous deserialization/eval patterns, and enforce trusted data boundaries.",
                "location": f"{item.get('file', 'unknown')}:{item.get('line', '?')}",
                "rule_id": str(item.get("rule_id", "AI")),
                "source_references": source_refs,
            }
        )
    return findings


def write_markdown_summary(
    run_timestamp_utc: str,
    scan_results: list[ScanResult],
    aggregated_findings: list[dict[str, Any]],
) -> str:
    timestamp_for_name = time.strftime("%Y%m%d-%H%M%SZ", time.gmtime())
    report_path = FINDINGS_DIR / f"security-summary-{timestamp_for_name}.md"

    by_severity: dict[str, list[dict[str, Any]]] = {level: [] for level in SEVERITY_ORDER}
    for finding in aggregated_findings:
        by_severity[normalize_severity(str(finding.get("severity", "medium")))].append(finding)

    lines: list[str] = []
    lines.append(f"# Security Scan Summary ({run_timestamp_utc})")
    lines.append("")
    lines.append("## Run Overview")
    lines.append("")
    lines.append(f"- Total findings: **{len(aggregated_findings)}**")
    lines.append(f"- Scanners executed: **{len(scan_results)}**")
    lines.append("")
    lines.append("## Findings By Severity")
    lines.append("")
    for level in SEVERITY_ORDER:
        lines.append(f"- {level.upper()}: **{len(by_severity[level])}**")
    lines.append("")

    for level in SEVERITY_ORDER:
        findings = by_severity[level]
        lines.append(f"## {level.upper()} Findings ({len(findings)})")
        lines.append("")
        if not findings:
            lines.append("_No findings in this severity bucket._")
            lines.append("")
            continue
        lines.append(
            "| Severity | Scanner | Rule ID | Issue | Location | Impact | Recommended Remediation | Source References |"
        )
        lines.append(
            "|---|---|---|---|---|---|---|---|"
        )
        for item in findings:
            refs = item.get("source_references", [])
            ref_text = ", ".join(
                f"{markdown_escape(str(ref.get('source', 'source')))} ({markdown_escape(str(ref.get('rule_id', 'id')))})"
                for ref in refs
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_escape(level.upper()),
                        markdown_escape(str(item.get("scanner", ""))),
                        markdown_escape(str(item.get("rule_id", ""))),
                        markdown_escape(str(item.get("title", ""))),
                        markdown_escape(str(item.get("location", ""))),
                        markdown_escape(str(item.get("impact", ""))),
                        markdown_escape(str(item.get("remediation", ""))),
                        markdown_escape(ref_text),
                    ]
                )
                + " |"
            )
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path.relative_to(REPO_ROOT))


@dataclass
class ScanResult:
    name: str
    command: list[str]
    exit_code: int
    duration_seconds: float
    output_file: str | None = None
    error: str | None = None


def run_command(
    name: str,
    command: list[str],
    output_log: Path,
    timeout_seconds: int = 180,
) -> ScanResult:
    start = time.time()
    try:
        process = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        elapsed = round(time.time() - start, 2)
        output_log.write_text(
            "\n".join(
                [
                    f"$ {' '.join(command)}",
                    "",
                    "STDOUT:",
                    process.stdout,
                    "",
                    "STDERR:",
                    process.stderr,
                ]
            ),
            encoding="utf-8",
        )
        return ScanResult(
            name=name,
            command=command,
            exit_code=process.returncode,
            duration_seconds=elapsed,
            output_file=str(output_log.relative_to(REPO_ROOT)),
        )
    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - start, 2)
        output_log.write_text(
            f"$ {' '.join(command)}\n\nSTDERR:\n{name} timed out after {timeout_seconds} seconds",
            encoding="utf-8",
        )
        return ScanResult(
            name=name,
            command=command,
            exit_code=2,
            duration_seconds=elapsed,
            output_file=str(output_log.relative_to(REPO_ROOT)),
            error=f"{name} timed out",
        )
    except Exception as exc:  # pragma: no cover - failure path
        elapsed = round(time.time() - start, 2)
        output_log.write_text(str(exc), encoding="utf-8")
        return ScanResult(
            name=name,
            command=command,
            exit_code=2,
            duration_seconds=elapsed,
            output_file=str(output_log.relative_to(REPO_ROOT)),
            error=str(exc),
        )


def normalize_secret_results(payload: dict[str, Any]) -> set[tuple[str, str, str]]:
    normalized: set[tuple[str, str, str]] = set()
    raw_results = payload.get("results", {})
    if not isinstance(raw_results, dict):
        return normalized

    for filename, findings in raw_results.items():
        if not isinstance(findings, list):
            continue
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            secret_hash = str(finding.get("hashed_secret", ""))
            finding_type = str(finding.get("type", ""))
            normalized.add((str(filename), finding_type, secret_hash))
    return normalized


def run_detect_secrets() -> tuple[ScanResult, int]:
    current_path = FINDINGS_DIR / "detect-secrets.current.json"
    delta_path = FINDINGS_DIR / "detect-secrets.delta.json"
    log_path = FINDINGS_DIR / "detect-secrets.log.txt"
    baseline_path = SECURITY_DIR / ".secrets.baseline"

    scan_targets = [
        path
        for path in [
            "coaching/src",
            "shared",
            "infrastructure",
            "deployment",
            ".github/workflows",
            "scripts",
        ]
        if (REPO_ROOT / path).exists()
    ]

    command = [
        PYTHON,
        "-m",
        "detect_secrets",
        "scan",
        "--exclude-files",
        DETECT_SECRETS_EXCLUDE_REGEX,
    ] + scan_targets

    start = time.time()
    try:
        process = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - start, 2)
        log_path.write_text(
            f"$ {' '.join(command)}\n\nSTDERR:\ndetect-secrets scan timed out after 300 seconds",
            encoding="utf-8",
        )
        return (
            ScanResult(
                name="detect-secrets",
                command=command,
                exit_code=2,
                duration_seconds=elapsed,
                output_file=str(log_path.relative_to(REPO_ROOT)),
                error="detect-secrets scan timed out",
            ),
            0,
        )
    elapsed = round(time.time() - start, 2)

    log_path.write_text(
        "\n".join(
            [
                f"$ {' '.join(command)}",
                "",
                "STDOUT:",
                process.stdout,
                "",
                "STDERR:",
                process.stderr,
            ]
        ),
        encoding="utf-8",
    )

    if process.returncode != 0:
        return (
            ScanResult(
                name="detect-secrets",
                command=command,
                exit_code=process.returncode,
                duration_seconds=elapsed,
                output_file=str(log_path.relative_to(REPO_ROOT)),
                error="detect-secrets execution failed",
            ),
            0,
        )

    try:
        current_payload: dict[str, Any] = json.loads(process.stdout)
    except json.JSONDecodeError:
        return (
            ScanResult(
                name="detect-secrets",
                command=command,
                exit_code=2,
                duration_seconds=elapsed,
                output_file=str(log_path.relative_to(REPO_ROOT)),
                error="Could not parse detect-secrets JSON output",
            ),
            0,
        )

    current_path.write_text(json.dumps(current_payload, indent=2), encoding="utf-8")

    if baseline_path.exists():
        approved_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    else:
        approved_payload = {"results": {}}

    approved = normalize_secret_results(approved_payload)
    current = normalize_secret_results(current_payload)

    new_findings = sorted(current - approved)
    delta_payload = {
        "new_findings_count": len(new_findings),
        "new_findings": [
            {"file": item[0], "type": item[1], "hashed_secret": item[2]} for item in new_findings
        ],
    }
    delta_path.write_text(json.dumps(delta_payload, indent=2), encoding="utf-8")

    exit_code = 1 if new_findings else 0
    return (
        ScanResult(
            name="detect-secrets",
            command=command,
            exit_code=exit_code,
            duration_seconds=elapsed,
            output_file=str(delta_path.relative_to(REPO_ROOT)),
            error=None if not new_findings else "New potential secrets detected",
        ),
        len(new_findings),
    )


def run_ai_risk_checks() -> ScanResult:
    findings_path = FINDINGS_DIR / "ai-risk-checks.json"
    log_path = FINDINGS_DIR / "ai-risk-checks.log.txt"
    start = time.time()

    findings: list[dict[str, Any]] = []
    scan_roots = [REPO_ROOT / "coaching" / "src", REPO_ROOT / "shared"]

    scanned_files = 0
    for root in scan_roots:
        if not root.exists():
            continue
        for file_path in root.rglob("*.py"):
            scanned_files += 1
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue

            for idx, line in enumerate(lines, start=1):
                for rule in AI_RISK_PATTERNS:
                    if rule["pattern"].search(line):
                        findings.append(
                            {
                                "rule_id": rule["id"],
                                "severity": rule["severity"],
                                "message": rule["message"],
                                "source_references": rule["source_references"],
                                "file": str(file_path.relative_to(REPO_ROOT)),
                                "line": idx,
                                "snippet": line.strip(),
                            }
                        )

    payload = {
        "scanner": "ai-risk-native",
        "scanned_files": scanned_files,
        "finding_count": len(findings),
        "findings": findings,
    }
    findings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log_path.write_text(
        f"Scanned files: {scanned_files}\nFindings: {len(findings)}\nOutput: {findings_path}",
        encoding="utf-8",
    )

    elapsed = round(time.time() - start, 2)
    return ScanResult(
        name="ai-risk-checks",
        command=["internal-ai-risk-check"],
        exit_code=1 if findings else 0,
        duration_seconds=elapsed,
        output_file=str(findings_path.relative_to(REPO_ROOT)),
        error=None if not findings else "AI risk patterns detected",
    )


def main() -> int:
    os.environ.setdefault("PYTHONUTF8", "1")
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)

    results: list[ScanResult] = []

    bandit_report = FINDINGS_DIR / "bandit.json"
    results.append(
        run_command(
            "bandit",
            [
                PYTHON,
                "-m",
                "bandit",
                "-r",
                "coaching/src",
                "shared",
                "-c",
                str(SECURITY_DIR / "bandit.yaml"),
                "-f",
                "json",
                "-o",
                str(bandit_report),
            ],
            FINDINGS_DIR / "bandit.log.txt",
        )
    )

    pip_audit_report = FINDINGS_DIR / "pip-audit.json"
    results.append(
        run_command(
            "pip-audit",
            [
                PYTHON,
                "-m",
                "pip_audit",
                "-r",
                "coaching/requirements.txt",
                "-r",
                "coaching/requirements-dev.txt",
                "--format",
                "json",
                "--output",
                str(pip_audit_report),
            ],
            FINDINGS_DIR / "pip-audit.log.txt",
        )
    )

    results.append(run_ai_risk_checks())

    scan_targets = [path for path in ["infrastructure", "deployment", ".github/workflows"] if (REPO_ROOT / path).exists()]
    if scan_targets:
        checkov_report = FINDINGS_DIR / "checkov.json"
        checkov_command = [
            PYTHON,
            "-m",
            "checkov.main",
            "--config-file",
            str(SECURITY_DIR / "checkov.yaml"),
            "--output",
            "json",
            "--output-file-path",
            str(checkov_report),
        ]
        for target in scan_targets:
            checkov_command.extend(["-d", target])

        results.append(run_command("checkov", checkov_command, FINDINGS_DIR / "checkov.log.txt"))

    detect_secrets_result, new_secret_count = run_detect_secrets()
    results.append(detect_secrets_result)

    run_timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    aggregated_findings = (
        parse_bandit_findings()
        + parse_pip_audit_findings()
        + parse_checkov_findings()
        + parse_detect_secrets_findings()
        + parse_ai_risk_findings()
    )
    report_file = write_markdown_summary(run_timestamp_utc, results, aggregated_findings)

    summary = {
        "timestamp_utc": run_timestamp_utc,
        "scan_count": len(results),
        "total_findings": len(aggregated_findings),
        "new_secret_findings": new_secret_count,
        "framework_reference_map": SCANNER_FRAMEWORK_MAPPINGS,
        "markdown_report": report_file,
        "results": [asdict(item) for item in results],
    }
    summary_path = FINDINGS_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    failed = [item for item in results if item.exit_code != 0]
    if failed:
        print("Security scans completed with findings/errors. See .artifacts/security/summary.json")
        return 1

    print("Security scans completed successfully. Reports written to .artifacts/security/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
