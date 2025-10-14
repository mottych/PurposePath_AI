# PowerShell script to run tests

param(
    [string]$Pattern = "",
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$OutputFile = ""
)

Write-Host "Running TrueNorth Coaching API tests..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path ".venv")) {
    Write-Error "Virtual environment not found. Please run setup.ps1 first."
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Set test environment variables
$env:STAGE = "test"
$env:LOG_LEVEL = "ERROR"
$env:AWS_REGION = "us-east-1"

# Build pytest command
$PytestArgs = @("tests/")

if ($Pattern) {
    $PytestArgs += "-k"
    $PytestArgs += $Pattern
}

if ($Verbose) {
    $PytestArgs += "-v"
}

if ($Coverage) {
    $PytestArgs += "--cov=src"
    $PytestArgs += "--cov-report=term-missing"
    $PytestArgs += "--cov-report=html:htmlcov"
}

if ($OutputFile) {
    $PytestArgs += "--junitxml=$OutputFile"
}

# Run tests
Write-Host "Running tests with command: uv run pytest $($PytestArgs -join ' ')" -ForegroundColor Cyan

try {
    uv run pytest @PytestArgs
    Write-Host "Tests completed successfully!" -ForegroundColor Green
} catch {
    Write-Error "Tests failed!"
    exit 1
}

if ($Coverage) {
    Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Cyan
}