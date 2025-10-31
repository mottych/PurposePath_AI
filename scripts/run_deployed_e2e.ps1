# Script to run E2E tests against deployed environment
# Gets fresh auth token and runs tests

Write-Host "=== PurposePath AI - Deployed E2E Tests ===" -ForegroundColor Cyan
Write-Host ""

# Get authentication token
Write-Host "Getting authentication token..." -ForegroundColor Yellow
$token = .venv\Scripts\python.exe scripts\get_e2e_token.py

if (-not $token) {
    Write-Host "ERROR: Failed to get authentication token" -ForegroundColor Red
    exit 1
}

Write-Host "Token obtained successfully" -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:E2E_API_URL = "https://api.dev.purposepath.app/coaching"
$env:E2E_AUTH_TOKEN = $token
$env:E2E_TENANT_ID = "f937af6d-ea49-4bb4-bd65-38ef496da252"
$env:E2E_USER_ID = "6ca4f578-a7e6-4f58-84e5-26cc089515df"

# Check AWS credentials
if (-not $env:AWS_PROFILE -and -not ($env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY)) {
    Write-Host "WARNING: AWS credentials not configured. Bedrock tests will be skipped." -ForegroundColor Yellow
}

# Check OpenAI credentials
if (-not $env:OPENAI_API_KEY) {
    Write-Host "WARNING: OPENAI_API_KEY not set. GPT-5 tests will be skipped." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Environment Configuration:" -ForegroundColor Cyan
Write-Host "  API URL: $env:E2E_API_URL" -ForegroundColor White
Write-Host "  Tenant ID: $env:E2E_TENANT_ID" -ForegroundColor White
Write-Host "  User ID: $env:E2E_USER_ID" -ForegroundColor White
Write-Host "  AWS: $(if ($env:AWS_PROFILE) { $env:AWS_PROFILE } else { 'Not configured' })" -ForegroundColor White
Write-Host "  OpenAI: $(if ($env:OPENAI_API_KEY) { 'Configured' } else { 'Not configured' })" -ForegroundColor White
Write-Host ""

# Parse command line arguments for test filter
$TestFilter = $args[0]

if ($TestFilter) {
    Write-Host "Running E2E tests matching: $TestFilter" -ForegroundColor Green
    Write-Host ""
    .venv\Scripts\python.exe -m pytest coaching/tests/e2e/ -v -m e2e -k $TestFilter --tb=short
} else {
    Write-Host "Running ALL E2E tests against deployed environment..." -ForegroundColor Green
    Write-Host ""
    .venv\Scripts\python.exe -m pytest coaching/tests/e2e/ -v -m e2e --tb=short
}

$ExitCode = $LASTEXITCODE

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "=== E2E Tests PASSED ===" -ForegroundColor Green
} else {
    Write-Host "=== E2E Tests FAILED (Exit Code: $ExitCode) ===" -ForegroundColor Red
}

exit $ExitCode
