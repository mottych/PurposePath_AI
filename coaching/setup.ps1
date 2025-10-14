# PowerShell setup script for Windows development with uv

Write-Host "Setting up TrueNorth Coaching Module with uv..." -ForegroundColor Green

# Check if uv is installed
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    # Install uv using PowerShell
    irm https://astral.sh/uv/install.ps1 | iex
    Write-Host "uv installed successfully!" -ForegroundColor Green
} else {
    Write-Host "uv is already installed" -ForegroundColor Cyan
}

# Create virtual environment using uv
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
uv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Sync dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
uv pip sync requirements.txt

# Install development dependencies
Write-Host "Installing development dependencies..." -ForegroundColor Yellow
uv pip install -e ".[dev]"

# Install serverless framework globally if not present
if (!(Get-Command serverless -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Serverless Framework..." -ForegroundColor Yellow
    npm install -g serverless
    npm install -g serverless-python-requirements
    npm install -g serverless-offline
    npm install -g serverless-dotenv-plugin
} else {
    Write-Host "Serverless Framework is already installed" -ForegroundColor Cyan
}

# Install local serverless plugins
Write-Host "Installing Serverless plugins..." -ForegroundColor Yellow
npm install --save-dev serverless-python-requirements
npm install --save-dev serverless-offline
npm install --save-dev serverless-dotenv-plugin

# Create .env file if it doesn't exist
if (!(Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Development Environment Variables
STAGE=dev
AWS_REGION=us-east-1
LOG_LEVEL=DEBUG
DYNAMODB_TABLE=truenorth-coaching-conversations-dev
PROMPTS_BUCKET=truenorth-coaching-prompts-dev
REDIS_HOST=localhost
REDIS_PORT=6379

# AWS Credentials (configure with 'aws configure' instead for production)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
"@ | Out-File -FilePath .env -Encoding UTF8
    Write-Host ".env file created. Please update with your AWS credentials." -ForegroundColor Yellow
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nTo activate the virtual environment in future sessions, run:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "`nTo run the development server:" -ForegroundColor Cyan
Write-Host "  uv run uvicorn src.api.main:app --reload --port 8000" -ForegroundColor White
Write-Host "`nTo deploy to AWS:" -ForegroundColor Cyan
Write-Host "  .\deploy.ps1 -stage dev" -ForegroundColor White