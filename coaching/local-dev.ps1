# PowerShell script to run local development server

param(
    [int]$Port = 8000,
    [switch]$Reload,
    [string]$LogLevel = "DEBUG"
)

Write-Host "Starting TrueNorth Coaching API development server..." -ForegroundColor Green

$CoachingRoot = $PSScriptRoot
Set-Location $CoachingRoot

$PythonExe = Join-Path $CoachingRoot ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $PythonExe)) {
    Write-Error "Virtual environment not found at coaching\.venv. Run setup.ps1 or: uv sync"
    exit 1
}
Write-Host "Using Python: $PythonExe" -ForegroundColor DarkGray

# Set environment variables
$env:STAGE = "dev"
$env:LOG_LEVEL = $LogLevel
$env:AWS_REGION = "us-east-1"

Write-Host "Starting FastAPI server on port $Port..." -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:$Port/docs" -ForegroundColor Yellow
Write-Host "Health Check: http://localhost:$Port/api/v1/health" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

# Start the server
$LogLevelArg = $LogLevel.ToLower()
if ($Reload) {
    & $PythonExe -m uvicorn src.api.main:app --host 0.0.0.0 --port $Port --reload --log-level $LogLevelArg
} else {
    & $PythonExe -m uvicorn src.api.main:app --host 0.0.0.0 --port $Port --log-level $LogLevelArg
}