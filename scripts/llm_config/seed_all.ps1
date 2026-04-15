# Master script to seed LLM configurations
#
# This script orchestrates the complete seeding process:
# 1. Validates code registries
# 2. Seeds templates to S3
# 3. Seeds configurations to DynamoDB
# 4. Validates entire system
#
# Usage:
#   .\scripts\llm_config\seed_all.ps1 -Environment dev
#   .\scripts\llm_config\seed_all.ps1 -Environment dev -TemplatesDir .\templates -Bucket purposepath-prompts-dev

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "production")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$TemplatesDir = ".\templates",
    
    [Parameter(Mandatory=$false)]
    [string]$Bucket = "purposepath-prompts-$Environment",
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = ".\configs\llm_configs_$Environment.yaml",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTemplates,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipConfigs,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"

$ScriptsDir = Split-Path -Parent $PSScriptRoot
$RepoRoot = (Resolve-Path (Split-Path -Parent $ScriptsDir)).Path
. (Join-Path $ScriptsDir "Resolve-CoachingPython.ps1")
$PythonExe = Get-CoachingPythonExecutable -RepoRoot $RepoRoot
if (-not $PythonExe) {
    Write-Host "❌ No coaching venv Python found" -ForegroundColor Red
    Write-Host "   Run: cd coaching && uv sync" -ForegroundColor Yellow
    exit 1
}

Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host "LLM Configuration Seeding - Environment: $Environment"
Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host ""
Write-Host "Using Python: $PythonExe" -ForegroundColor DarkGray
Write-Host ""

Push-Location $RepoRoot
try {
# Step 1: Verify code registries
Write-Host "Step 1: Verifying code registries..." -ForegroundColor Cyan
& $PythonExe -c @"
from coaching.src.core.llm_interactions import INTERACTION_REGISTRY
from coaching.src.core.llm_models import MODEL_REGISTRY
print(f'✓ {len(INTERACTION_REGISTRY)} interactions in registry')
print(f'✓ {len(MODEL_REGISTRY)} models in registry')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Code registry verification failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Seed templates
if (-not $SkipTemplates) {
    Write-Host "Step 2: Seeding templates to S3..." -ForegroundColor Cyan
    
    if (-not (Test-Path $TemplatesDir)) {
        Write-Host "⚠️  Templates directory not found: $TemplatesDir" -ForegroundColor Yellow
        Write-Host "   Skipping template seeding" -ForegroundColor Yellow
    }
    else {
        & $PythonExe scripts\llm_config\seed_templates.py `
            --templates-dir $TemplatesDir `
            --bucket $Bucket `
            --environment $Environment `
            --region $Region
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Template seeding failed" -ForegroundColor Red
            exit 1
        }
    }
}
else {
    Write-Host "Step 2: Skipping template seeding (--SkipTemplates)" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Seed configurations
if (-not $SkipConfigs) {
    Write-Host "Step 3: Seeding configurations to DynamoDB..." -ForegroundColor Cyan
    
    if (-not (Test-Path $ConfigFile)) {
        Write-Host "⚠️  Configuration file not found: $ConfigFile" -ForegroundColor Yellow
        Write-Host "   Skipping configuration seeding" -ForegroundColor Yellow
    }
    else {
        & $PythonExe scripts\llm_config\seed_configurations.py `
            --config-file $ConfigFile `
            --environment $Environment `
            --region $Region
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Configuration seeding failed" -ForegroundColor Red
            exit 1
        }
    }
}
else {
    Write-Host "Step 3: Skipping configuration seeding (--SkipConfigs)" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Validate system
if (-not $SkipValidation) {
    Write-Host "Step 4: Validating LLM configuration system..." -ForegroundColor Cyan
    
    & $PythonExe scripts\llm_config\validate_configuration.py `
        --environment $Environment `
        --bucket $Bucket `
        --region $Region
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Validation failed" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "Step 4: Skipping validation (--SkipValidation)" -ForegroundColor Yellow
}
Write-Host ""

} finally {
    Pop-Location
}

# Success!
Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host "✅ LLM Configuration Seeding Complete!" -ForegroundColor Green
Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review validation results above"
Write-Host "  2. Test configuration system with: & `"$PythonExe`" -m pytest coaching/tests/"
Write-Host "  3. Enable feature flag: use_llm_config_system=True"
Write-Host "  4. Deploy to $Environment environment"
Write-Host ""

exit 0
