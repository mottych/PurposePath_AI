# PurposePath Platform Setup Script (Windows)
# This script sets up the complete monorepo for development

Write-Host "🚀 Setting up PurposePath Platform Monorepo..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Git
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Check .NET
if (!(Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "❌ .NET SDK is not installed. Please install .NET 8 SDK first." -ForegroundColor Red
    exit 1
}

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites are installed" -ForegroundColor Green

# Clone repository if not already cloned
if (!(Test-Path ".git")) {
    Write-Host "📁 Cloning PurposePath repository..." -ForegroundColor Yellow
    git clone https://github.com/mottych/PurposePath_Api.git .
    
    Write-Host "🔄 Switching to platform-monorepo branch..." -ForegroundColor Yellow
    git checkout platform-monorepo
} else {
    Write-Host "📁 Repository already exists, updating..." -ForegroundColor Yellow
    git fetch origin
    git checkout platform-monorepo
    git pull origin platform-monorepo
}

# Initialize submodules
Write-Host "🔧 Initializing git submodules..." -ForegroundColor Yellow
git submodule init
git submodule update

# Setup .NET API
Write-Host "🏗️ Setting up .NET API services..." -ForegroundColor Yellow
Set-Location pp_api
dotnet restore
dotnet build --configuration Release --warnaserror

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ .NET API services built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ .NET API build failed" -ForegroundColor Red
    exit 1
}

# Run .NET tests
Write-Host "🧪 Running .NET tests..." -ForegroundColor Yellow
dotnet test --no-build --configuration Release

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All .NET tests passed" -ForegroundColor Green
} else {
    Write-Host "❌ Some .NET tests failed" -ForegroundColor Red
    exit 1
}

# Setup Python AI services
Write-Host "🐍 Setting up Python AI services..." -ForegroundColor Yellow
Set-Location ..\pp_ai_submodule

# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    python -m venv venv
}

# Activate virtual environment and install dependencies
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Write-Host "✅ Python AI services setup completed" -ForegroundColor Green

# Return to root
Set-Location ..

Write-Host ""
Write-Host "🎉 PurposePath Platform Setup Complete!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "📂 Repository Structure:" -ForegroundColor Cyan
Write-Host "  ├── pp_api/           (.NET 8 Account Services)"
Write-Host "  ├── pp_ai_submodule/  (Python AI Services)"
Write-Host "  └── docs/            (Platform Documentation)"
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review docs/MIGRATION_STATUS.md for platform overview"
Write-Host "  2. Check docs/GIT_WORKFLOW.md for development workflow"
Write-Host "  3. Start developing with the unified platform!"
Write-Host ""
Write-Host "💡 Development Commands:" -ForegroundColor Cyan
Write-Host "  .NET API: cd pp_api && dotnet run"
Write-Host "  Python AI: cd pp_ai_submodule && python main.py"
Write-Host ""