# Security Automation

Security scanning for this repository is orchestrated by:

- `security/run_security_scans.py`

All scanner outputs are machine-readable and written to:

- `.artifacts/security/`

Local entrypoint:

```powershell
.\scripts\security-scan.ps1
```

Scanner dependencies are pinned in:

- `security/requirements-security.txt`

AI-specific checks are implemented in:

- `security/run_security_scans.py` (`AI_RISK_PATTERNS`)

Operational runbook:

- `docs/local/security/security-scanning-runbook.md`
