# Script to run E2E tests with proper environment setup
# Usage: .\scripts\run_e2e_tests.ps1

Write-Host "=== PurposePath AI E2E Test Runner ===" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python virtual environment
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found. Run 'python -m venv .venv' first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
if (-not $env:AWS_PROFILE -and -not ($env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY)) {
    Write-Host "WARNING: AWS credentials not configured. Bedrock tests will be skipped." -ForegroundColor Yellow
    Write-Host "  Set AWS_PROFILE or AWS credentials environment variables." -ForegroundColor Yellow
}

# Check OpenAI API key
if (-not $env:OPENAI_API_KEY) {
    Write-Host "WARNING: OPENAI_API_KEY not set. GPT-5 tests will be skipped." -ForegroundColor Yellow
}

# Check Google credentials
if (-not $env:GOOGLE_PROJECT_ID) {
    Write-Host "WARNING: GOOGLE_PROJECT_ID not set. Gemini tests will be skipped." -ForegroundColor Yellow
}

# Check API endpoint
if (-not $env:E2E_API_URL) {
    Write-Host "INFO: E2E_API_URL not set. Using default: http://localhost:8000" -ForegroundColor Cyan
    $env:E2E_API_URL = "http://localhost:8000"
}

# Check auth token
if (-not $env:E2E_AUTH_TOKEN) {
    Write-Host "WARNING: E2E_AUTH_TOKEN not set. Authentication tests will be skipped." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Environment Configuration:" -ForegroundColor Cyan
Write-Host "  API URL: $env:E2E_API_URL" -ForegroundColor White
Write-Host "  AWS: $(if ($env:AWS_PROFILE) { 'Configured' } else { 'Not configured' })" -ForegroundColor White
Write-Host "  OpenAI: $(if ($env:OPENAI_API_KEY) { 'Configured' } else { 'Not configured' })" -ForegroundColor White
Write-Host "  Google: $(if ($env:GOOGLE_PROJECT_ID) { 'Configured' } else { 'Not configured' })" -ForegroundColor White
Write-Host ""

# Parse command line arguments
$TestFilter = $args[0]

if ($TestFilter) {
    Write-Host "Running E2E tests matching: $TestFilter" -ForegroundColor Green
    .venv\Scripts\python.exe -m pytest coaching/tests/e2e/ -v -m e2e -k $TestFilter
} else {
    Write-Host "Running all E2E tests..." -ForegroundColor Green
    .venv\Scripts\python.exe -m pytest coaching/tests/e2e/ -v -m e2e
}

$ExitCode = $LASTEXITCODE

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "=== E2E Tests PASSED ===" -ForegroundColor Green
} else {
    Write-Host "=== E2E Tests FAILED ===" -ForegroundColor Red
}

exit $ExitCode
