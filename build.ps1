param(
    [string]$Stage = "dev"
)

Write-Host "Building Coaching Service..." -ForegroundColor Cyan

# Activate virtual environment
& .venv\Scripts\Activate.ps1

# Set Docker API version to fix SAM CLI compatibility issue
$env:DOCKER_API_VERSION = "1.44"

Set-Location coaching
sam build --template template.yaml

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Set-Location ..
