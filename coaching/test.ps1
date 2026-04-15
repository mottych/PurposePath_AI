# PowerShell script to run tests and validation

param(
    [string]$Pattern = "",
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$OutputFile = "",
    [switch]$SkipValidation
)

Write-Host "Running TrueNorth Coaching API tests and validation..." -ForegroundColor Green

$CoachingRoot = $PSScriptRoot
$PythonExe = Join-Path $CoachingRoot ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $PythonExe)) {
    Write-Error "Virtual environment not found at coaching\.venv. Run setup.ps1 or: uv sync"
    exit 1
}
Write-Host "Using Python: $PythonExe" -ForegroundColor DarkGray

Push-Location $CoachingRoot
try {

# Run validation steps unless skipped
if (-not $SkipValidation) {
    Write-Host "`n=== Running Code Validation ===" -ForegroundColor Cyan
    
    # Run Black formatting check
    Write-Host "`nChecking code formatting with Black..." -ForegroundColor Yellow
    & $PythonExe -m black --check src/ tests/
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Black formatting check failed. Run 'black src/ tests/' to fix."
        exit 1
    }
    Write-Host "✓ Black formatting check passed" -ForegroundColor Green
    
    # Run Ruff linting
    Write-Host "`nRunning Ruff linting..." -ForegroundColor Yellow
    & $PythonExe -m ruff check src/ tests/ --exclude=".venv,venv,__pycache__,.pytest_cache"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Ruff linting failed."
        exit 1
    }
    Write-Host "✓ Ruff linting passed" -ForegroundColor Green
    
    # Run MyPy type checking with strict mode
    Write-Host "`nRunning MyPy type checking (strict mode)..." -ForegroundColor Yellow
    & $PythonExe -m mypy src/ ..\shared\ --config-file=..\pyproject.toml --strict
    if ($LASTEXITCODE -ne 0) {
        Write-Error "MyPy type checking failed."
        exit 1
    }
    Write-Host "✓ MyPy type checking passed" -ForegroundColor Green
    
    Write-Host "`n=== All Validation Checks Passed ===" -ForegroundColor Green
}

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
Write-Host "`n=== Running Unit Tests ===" -ForegroundColor Cyan
Write-Host "Running tests: & `"$PythonExe`" -m pytest $($PytestArgs -join ' ')" -ForegroundColor Cyan

try {
    & $PythonExe -m pytest @PytestArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tests failed!"
        exit 1
    }
    Write-Host "`n✓ Tests completed successfully!" -ForegroundColor Green
} catch {
    Write-Error "Tests failed!"
    exit 1
}

if ($Coverage) {
    Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Cyan
}

Write-Host "`n=== All Checks Completed Successfully ===" -ForegroundColor Green

} finally {
    Pop-Location
}