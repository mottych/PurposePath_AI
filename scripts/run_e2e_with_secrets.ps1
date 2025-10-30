# Run E2E tests with secrets from AWS Secrets Manager

Write-Host "=== Loading secrets from AWS Secrets Manager ===" -ForegroundColor Cyan
Write-Host ""

# Get OpenAI API Key
Write-Host "Retrieving OpenAI API key..." -ForegroundColor Yellow
$openaiSecret = aws secretsmanager get-secret-value --secret-id purposepath/openai-api-key --region us-east-1 --query SecretString --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    $env:OPENAI_API_KEY = $openaiSecret
    Write-Host "✓ OpenAI API key loaded" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to load OpenAI API key: $openaiSecret" -ForegroundColor Red
}

Write-Host ""

# Run the deployed E2E tests
.\scripts\run_deployed_e2e.ps1
