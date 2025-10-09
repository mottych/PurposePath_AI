# PowerShell script to run local development server

param(
    [int]$Port = 8000,
    [switch]$Reload,
    [string]$LogLevel = "DEBUG"
)

Write-Host "Starting TrueNorth Coaching API development server..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path ".venv")) {
    Write-Error "Virtual environment not found. Please run setup.ps1 first."
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Set environment variables
$env:STAGE = "dev"
$env:LOG_LEVEL = $LogLevel
$env:AWS_REGION = "us-east-1"

Write-Host "Starting FastAPI server on port $Port..." -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:$Port/docs" -ForegroundColor Yellow
Write-Host "Health Check: http://localhost:$Port/api/v1/health" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

# Start the server
if ($Reload) {
    uv run uvicorn src.api.main:app --host 0.0.0.0 --port $Port --reload --log-level $LogLevel.ToLower()
} else {
    uv run uvicorn src.api.main:app --host 0.0.0.0 --port $Port --log-level $LogLevel.ToLower()
}