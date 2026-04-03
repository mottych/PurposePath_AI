# Security Scanning Runbook

This repository uses a security scan orchestrator at `security/run_security_scans.py`.
All machine-readable outputs are written to `.artifacts/security/`.

## Scope

The process covers:

- Static/security linting for Python source via `bandit`
- Dependency vulnerability analysis via `pip-audit`
- Secret scanning with triage baseline support via `detect-secrets`
- Infrastructure/config scanning via `checkov` (CloudFormation and GitHub Actions)
- AI-specific secure coding checks via native rule-based scanner (`ai-risk-checks`)

## One-command local execution

Run from repository root:

```powershell
.\scripts\security-scan.ps1
```

The script:

1. Creates/reuses `.venv-security` (repo-scoped)
2. Installs pinned scanner versions from `security/requirements-security.txt`
3. Runs `python security/run_security_scans.py`

## CI automation

Workflow: `.github/workflows/security-scans.yml`

Triggers:

- Pull requests to `dev`, `staging`, `preprod`, `master`
- Pushes to `dev`, `staging`, `preprod`, `master`
- Weekly scheduled run (`cron: 15 5 * * 1`)
- Manual (`workflow_dispatch`)

Artifacts:

- Uploaded from `.artifacts/security/`
- Includes machine-readable scanner outputs and a human-readable markdown summary

## Findings outputs

Generated machine-readable files under `.artifacts/security/` include:

- `summary.json` (aggregate status)
- `bandit.json`
- `pip-audit.json`
- `detect-secrets.current.json`
- `detect-secrets.delta.json`
- `checkov.json`
- `ai-risk-checks.json`
- `security-summary-YYYYMMDD-HHMMSSZ.md` (one markdown report per run)

Plain-text execution logs are also written per scanner for debugging.

`summary.json` also includes `framework_reference_map`, which maps each scanner to
its governance/control source references with IDs (for example OWASP, SOC 2, and
AWS Well-Architected rule identifiers).

Each markdown summary report groups findings by severity and, for each finding,
includes:

- Severity
- Short issue description
- Impact
- Recommended remediation
- Source rule/recommendation references (including IDs)

## Noise reduction strategy

Scanners exclude non-code or generated/editor/cache/model-adjacent noise through:

- `security/bandit.yaml` exclusions
- `security/checkov.yaml` `skip-path` entries
- `detect-secrets` exclude regex in `security/run_security_scans.py`

Default exclusions cover virtualenvs, caches, docs, tests, node modules, and generated findings.

## Baseline and triage governance

Baseline file:

- `security/.secrets.baseline`

Policy:

1. New findings are compared against the baseline in `run_security_scans.py`.
2. Only findings not present in baseline are treated as failures.
3. Baseline changes must be reviewed in PR with justification.

Governance notes:

- Keep baseline entries minimal and time-bound.
- Add a short PR note for each added baseline item: reason, owner, expiration/revisit date.
- Prefer fixing root causes over baseline expansion.

To regenerate baseline after triage:

```bash
python -m detect_secrets scan coaching/src shared infrastructure deployment .github/workflows scripts > security/.secrets.baseline
```

Then rerun:

```powershell
.\scripts\security-scan.ps1
```

## Maintenance checklist

- Monthly: review `security/requirements-security.txt` for patch-level updates.
- Quarterly: review `AI_RISK_PATTERNS` in `security/run_security_scans.py` against current AI stack usage.
- After repo structure changes: refresh exclusion patterns.
- After major dependency updates: re-run full scan and review delta.
