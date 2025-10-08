param(
  [string]$HostedZoneId,
  [string]$Region = 'us-east-1'
)

Write-Host "Deploying dev API domain..." -ForegroundColor Cyan
sam deploy `
  --template-file infra/api-domain-dev.yaml `
  --stack-name purposepath-api-domain-dev `
  --capabilities CAPABILITY_IAM `
  --parameter-overrides DomainName=api.dev.purposepath.app HostedZoneId=$HostedZoneId `
  --region $Region `
  --resolve-s3 `
  --no-confirm-changeset

$certArn = aws cloudformation describe-stacks --stack-name purposepath-api-domain-dev --region $Region `
  --query "Stacks[0].Outputs[?OutputKey=='CertificateArn'].OutputValue" --output text
Write-Host "CertificateArn: $certArn" -ForegroundColor Yellow

Write-Host "Deploying account (dev)..." -ForegroundColor Cyan
sam deploy `
  --template-file account/template-standalone.yaml `
  --stack-name purposepath-account-api-dev `
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND `
  --parameter-overrides Stage=dev LogLevel=DEBUG EmailFrom=dev@purposepath.ai JwtSecretArn=$(aws secretsmanager list-secrets --region $Region --query "SecretList[?Name=='purposepath/jwt-secret/dev'].ARN | [0]" --output text) NameSuffix=-v2 EnableCustomDomain=false ApiMappingKey=account `
  --region $Region `
  --resolve-s3 `
  --no-confirm-changeset

Write-Host "Deploying coaching (dev)..." -ForegroundColor Cyan
# Build image-based function first
sam build `
  --template coaching/template-standalone.yaml

# Discover Redis (dev) endpoint automatically if available
$redisEndpoint = ''
try {
  $rg = aws elasticache describe-replication-groups --region $Region `
    --query "ReplicationGroups[?contains(ReplicationGroupId, 'dev') || contains(ReplicationGroupId, 'purposepath')]|[0].{A:NodeGroups[0].PrimaryEndpoint.Address,P:NodeGroups[0].PrimaryEndpoint.Port}" --output json | ConvertFrom-Json
  if ($rg -and $rg.A -and $rg.P) { $redisEndpoint = "$($rg.A):$($rg.P)" }
} catch {}

# Discover VPC private subnets and Lambda SG from unified stack
$subnetsCsv = ''
$lambdaSg = ''
try {
  $subs = aws ec2 describe-subnets --region $Region --filters Name=tag:Name,Values=purposepath-private-subnet-1-dev,purposepath-private-subnet-2-dev `
    --query "Subnets[].SubnetId" --output text
  if ($subs) { $subnetsCsv = ($subs -split '\s+') -join ',' }
  $lambdaSg = aws ec2 describe-security-groups --region $Region `
    --filters Name=group-name,Values='purposepath-api-dev-LambdaSecurityGroup-*' --query 'SecurityGroups[0].GroupId' --output text
} catch {}

sam deploy `
  --template-file coaching/.aws-sam/build/template.yaml `
  --stack-name purposepath-coaching-api-dev `
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND `
  --parameter-overrides Stage=dev LogLevel=DEBUG JwtSecretArn=$(aws secretsmanager list-secrets --region $Region --query "SecretList[?Name=='purposepath/jwt-secret/dev'].ARN | [0]" --output text) NameSuffix=-v2 EnableCustomDomain=false ApiMappingKey=coaching RedisClusterEndpoint=$redisEndpoint RedisSSL=false SubnetIds=$subnetsCsv LambdaSecurityGroupIds=$lambdaSg `
  --region $Region `
  --resolve-s3 `
  --resolve-image-repos `
  --no-confirm-changeset

# Get API IDs and create domain mappings centrally
$accountApiId = aws cloudformation describe-stack-resources --stack-name purposepath-account-api-dev --region $Region `
  --query "StackResources[?ResourceType=='AWS::ApiGatewayV2::Api' && contains(LogicalResourceId,'AccountHttpApi')].PhysicalResourceId" --output text
$coachingApiId = aws cloudformation describe-stack-resources --stack-name purposepath-coaching-api-dev --region $Region `
  --query "StackResources[?ResourceType=='AWS::ApiGatewayV2::Api' && contains(LogicalResourceId,'CoachingHttpApi')].PhysicalResourceId" --output text

Write-Host "Cleaning existing API mappings (if any)..." -ForegroundColor Cyan
$existing = @()
try { $existing = aws apigatewayv2 get-api-mappings --domain-name api.dev.purposepath.app --region $Region | ConvertFrom-Json | Select-Object -ExpandProperty Items } catch {}
foreach ($m in $existing) {
  if ($m.ApiMappingKey -in @('account','coaching')) {
    aws apigatewayv2 delete-api-mapping --api-mapping-id $m.ApiMappingId --domain-name api.dev.purposepath.app --region $Region | Out-Null
  }
}

# Ensure mapping stack can be recreated
try { aws cloudformation delete-stack --stack-name purposepath-api-domain-mapping-dev --region $Region } catch {}
Start-Sleep -Seconds 5

Write-Host "Mapping /account and /coaching on api.dev..." -ForegroundColor Cyan
sam deploy `
  --template-file infra/api-domain-dev-mapping.yaml `
  --stack-name purposepath-api-domain-mapping-dev `
  --capabilities CAPABILITY_IAM `
  --parameter-overrides DomainName=api.dev.purposepath.app AccountApiId=$accountApiId CoachingApiId=$coachingApiId `
  --region $Region `
  --resolve-s3 `
  --no-confirm-changeset

$domain = aws cloudformation describe-stacks --stack-name purposepath-api-domain-dev --region $Region `
  --query "Stacks[0].Outputs[?OutputKey=='DomainName'].OutputValue" --output text
Write-Host "Dev API domain is https://$domain" -ForegroundColor Green
