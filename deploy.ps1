param(
    [string]$Stage = "dev",
    [string]$Region = "us-east-1",
    [string]$HostedZoneId = "Z02314942PKXY3PDDO5T"
)

Write-Host "PurposePath AI Coaching Service Deployment - $Stage" -ForegroundColor Green

$domainName = "api.dev.purposepath.app"

Write-Host "Deploying to: $Stage" -ForegroundColor Cyan
Write-Host "Domain: $domainName" -ForegroundColor Cyan

Write-Host "Deploying Coaching Service..." -ForegroundColor Cyan
Set-Location coaching
sam build --template template.yaml
sam deploy --template-file .aws-sam/build/template.yaml --stack-name purposepath-coaching-api-$Stage --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --parameter-overrides Stage=$Stage EnableCustomDomain=true CustomDomainName=$domainName --region $Region --resolve-s3 --resolve-image-repos --no-confirm-changeset
Set-Location ..

Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "Endpoint: https://$domainName/coaching/api/v1/" -ForegroundColor Yellow