param(
    [string]$Stage = "dev",
    [string]$Region = "us-east-1",
    [string]$HostedZoneId = "Z09156212RNBEXAMPLE"
)

Write-Host "🚀 PurposePath AI Coaching Service Deployment - $Stage" -ForegroundColor Green

# Set environment-specific domain names
$domainName = switch ($Stage) {
    "dev" { "ai-coaching.dev.purposepath.app" }
    "staging" { "ai-coaching.staging.purposepath.app" } 
    "production" { "ai-coaching.purposepath.app" }
    default { "ai-coaching.$Stage.purposepath.app" }
}

$domainTemplate = switch ($Stage) {
    "production" { "infra/api-domain-production.yaml" }
    "staging" { "infra/api-domain-staging.yaml" }
    default { "infra/api-domain-dev-mapping.yaml" }
}

Write-Host "Deploying to environment: $Stage" -ForegroundColor Cyan
Write-Host "Domain: $domainName" -ForegroundColor Cyan

# 1. Deploy Custom Domain
Write-Host "1. Setting up Custom Domain..." -ForegroundColor Cyan
try {
    aws apigatewayv2 get-domain-name --domain-name $domainName --region $Region | Out-Null
    Write-Host "   ✓ Domain exists" -ForegroundColor Green
}
catch {
    Write-Host "   Creating domain..." -ForegroundColor Yellow
    sam deploy --template-file $domainTemplate --stack-name purposepath-ai-domain-$Stage --capabilities CAPABILITY_IAM --parameter-overrides DomainName=$domainName HostedZoneId=$HostedZoneId --region $Region --resolve-s3 --no-confirm-changeset
}

# 2. Deploy Coaching Service  
Write-Host "2. Deploying AI Coaching Service..." -ForegroundColor Cyan
Set-Location coaching
sam build --template template.yaml
sam deploy --template-file .aws-sam/build/template.yaml --stack-name purposepath-coaching-api-$Stage --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --parameter-overrides Stage=$Stage --region $Region --resolve-s3 --resolve-image-repos --no-confirm-changeset
Set-Location ..

# 3. Setup API Mappings
Write-Host "3. Setting up API Mappings..." -ForegroundColor Cyan
$coachingApiId = aws cloudformation describe-stack-resources --stack-name purposepath-coaching-api-$Stage --region $Region --query "StackResources[?ResourceType=='AWS::ApiGatewayV2::Api'].PhysicalResourceId" --output text

# Clean existing mappings
$existing = @()
try { $existing = aws apigatewayv2 get-api-mappings --domain-name $domainName --region $Region | ConvertFrom-Json | Select-Object -ExpandProperty Items } catch {}
foreach ($m in $existing) {
    if ($m.ApiMappingKey -eq 'coaching') {
        aws apigatewayv2 delete-api-mapping --api-mapping-id $m.ApiMappingId --domain-name $domainName --region $Region | Out-Null
    }
}

# Create new mapping
aws apigatewayv2 create-api-mapping --domain-name $domainName --api-id $coachingApiId --stage $default --api-mapping-key coaching --region $Region | Out-Null

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 AI Coaching Endpoint:" -ForegroundColor Cyan
Write-Host "   Coaching: https://$domainName/coaching/api/v1/" -ForegroundColor Yellow