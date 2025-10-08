param([string]$Stage = "dev")

Write-Host "Deploying .NET Account Service - $Stage" -ForegroundColor Green

# Deploy Lambda
sam deploy --template-file account/template.yaml --stack-name purposepath-account-dotnet-$Stage --capabilities CAPABILITY_IAM --parameter-overrides Stage=$Stage --region us-east-1 --resolve-s3 --no-confirm-changeset

# Get API ID and update domain mapping
$apiId = aws cloudformation describe-stack-resources --stack-name purposepath-account-dotnet-$Stage --query "StackResources[?ResourceType=='AWS::ApiGatewayV2::Api'].PhysicalResourceId" --output text

# Remove old mapping
try { 
    $existing = aws apigatewayv2 get-api-mappings --domain-name api.$Stage.purposepath.app | ConvertFrom-Json
    $existing.Items | Where-Object { $_.ApiMappingKey -eq "account" } | ForEach-Object { 
        aws apigatewayv2 delete-api-mapping --api-mapping-id $_.ApiMappingId --domain-name api.$Stage.purposepath.app | Out-Null 
    }
} catch {}

# Create new mapping
aws apigatewayv2 create-api-mapping --domain-name api.$Stage.purposepath.app --api-id $apiId --stage '$default' --api-mapping-key account | Out-Null

Write-Host "Deployed: https://api.$Stage.purposepath.app/account/api/v1/" -ForegroundColor Yellow