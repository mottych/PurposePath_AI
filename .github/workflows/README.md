# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and deployment.

## Workflows

### `ci.yml` - Main CI/CD Pipeline

**Triggers:**
- Push to `dev` or `main` branches
- Pull requests targeting `dev` or `main`

**Jobs:**

#### 1. Lint and Test
Runs on Python 3.11 and 3.12 to ensure compatibility.

**Steps:**
- ✅ **Ruff Linting** - Code style and quality checks
- ✅ **Ruff Format Check** - Ensures code is properly formatted
- ⚠️ **MyPy Type Checking** - Static type analysis (warnings only)
- ✅ **Pytest Unit Tests** - Runs all unit tests with coverage reporting

**Notes:**
- Type checking errors won't fail the build (set to `continue-on-error: true`)
- Test coverage is uploaded to Codecov (if token is configured)
- Pip dependencies are cached for faster builds

#### 2. Security Scan
Runs security analysis on the codebase.

**Steps:**
- ✅ **Bandit** - Python security vulnerability scanner
- ✅ **Safety** - Checks for known security vulnerabilities in dependencies

**Notes:**
- Security warnings won't fail the build initially
- Recommended to review and fix security issues promptly

#### 3. Deploy Ready Check
Confirms deployment readiness for `main` branch.

**Conditions:**
- Only runs on `main` branch
- Requires all previous jobs to pass
- Provides deployment status summary

---

## Configuration

### Secrets Required

For full functionality, configure these secrets in GitHub repository settings:

- `CODECOV_TOKEN` (Optional) - For test coverage reports at codecov.io

### Environment Variables

The workflow sets:
- `PYTHONPATH` - Ensures proper module resolution during tests

---

## Local Testing

To run the same checks locally before pushing:

```bash
# Linting
python -m ruff check coaching/ shared/

# Format check
python -m ruff format --check coaching/ shared/

# Type checking
python -m mypy coaching/src shared/ --explicit-package-bases

# Unit tests with coverage
python -m pytest coaching/tests/unit -v --cov=coaching/src --cov=shared

# Security scan
pip install bandit[toml] safety
bandit -r coaching/src shared/ -ll
safety check
```

---

## Status Badges

Add to your main README.md:

```markdown
![CI/CD Pipeline](https://github.com/mottych/PurposePath_AI/actions/workflows/ci.yml/badge.svg)
```

---

## Troubleshooting

### Build Fails on Dependency Installation
- Check that `requirements.txt` and `requirements-dev.txt` are up to date
- Ensure all dependencies are compatible with Python 3.11+

### Tests Fail in CI but Pass Locally
- Verify `PYTHONPATH` is set correctly
- Check for environment-specific configurations
- Ensure test fixtures don't rely on local files

### Type Checking Warnings
- Type warnings are informational only (won't fail build)
- Address them gradually to improve code quality

---

## Future Enhancements

Potential additions:
- [ ] Integration tests job
- [ ] Deploy to AWS Lambda on `main` push
- [ ] Automated dependency updates (Dependabot)
- [ ] Performance benchmarking
- [ ] Docker image building
- [ ] Notification on failures (Slack/Email)

---

**Last Updated:** October 21, 2025
