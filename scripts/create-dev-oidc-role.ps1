param(
  [string]$GitHubOrg = '',
  [string]$Repo = '',
  [string]$Region = 'us-east-1'
)

Write-Host "Ensuring GitHub OIDC provider..." -ForegroundColor Cyan
$providerArn = (aws iam list-open-id-connect-providers | ConvertFrom-Json).OpenIDConnectProviderList | Where-Object { $_.Arn -like '*token.actions.githubusercontent.com*' } | Select-Object -First 1 -ExpandProperty Arn
if (-not $providerArn) {
  aws iam create-open-id-connect-provider `
    --url https://token.actions.githubusercontent.com `
    --client-id-list sts.amazonaws.com `
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 | Out-Null
  $providerArn = (aws iam list-open-id-connect-providers | ConvertFrom-Json).OpenIDConnectProviderList | Where-Object { $_.Arn -like '*token.actions.githubusercontent.com*' } | Select-Object -First 1 -ExpandProperty Arn
}
Write-Host "OIDC Provider: $providerArn" -ForegroundColor Yellow

$roleName = 'purposepath-dev-deployer'
Write-Host "Creating IAM role $roleName ..." -ForegroundColor Cyan

$subCondition = if ($GitHubOrg -and $Repo) { "repo:${GitHubOrg}/${Repo}:*" } elseif ($GitHubOrg) { "repo:${GitHubOrg}/*:*" } else { "repo:*" }

$trust = @{
  Version = '2012-10-17'
  Statement = @(
    @{ Effect='Allow'; Principal=@{ Federated=$providerArn }; Action='sts:AssumeRoleWithWebIdentity'; Condition=@{ StringEquals=@{ 'token.actions.githubusercontent.com:aud'='sts.amazonaws.com' }; StringLike=@{ 'token.actions.githubusercontent.com:sub'=$subCondition } } }
  )
} | ConvertTo-Json -Depth 5

aws iam create-role --role-name $roleName --assume-role-policy-document $trust | Out-Null

Write-Host "Attaching least-privilege inline policy..." -ForegroundColor Cyan
$policy = @{
  Version='2012-10-17'
  Statement=@(
    @{ Effect='Allow'; Action=@('cloudformation:*'); Resource='*' },
    @{ Effect='Allow'; Action=@('apigateway:*','execute-api:*'); Resource='*' },
    @{ Effect='Allow'; Action=@('dynamodb:*'); Resource='*' },
    @{ Effect='Allow'; Action=@('secretsmanager:GetSecretValue','secretsmanager:DescribeSecret'); Resource='*' },
    @{ Effect='Allow'; Action=@('acm:*'); Resource='*' },
    @{ Effect='Allow'; Action=@('route53:*'); Resource='*' },
    @{ Effect='Allow'; Action=@('lambda:*'); Resource='*' },
    @{ Effect='Allow'; Action=@('logs:*','s3:*','iam:PassRole'); Resource='*' }
  )
} | ConvertTo-Json -Depth 5

aws iam put-role-policy --role-name $roleName --policy-name purposepath-dev-deploy --policy-document $policy | Out-Null

$roleArn = aws iam get-role --role-name $roleName | ConvertFrom-Json | Select-Object -ExpandProperty Role | Select-Object -ExpandProperty Arn
Write-Host "Created role: $roleArn" -ForegroundColor Green
Write-Host "Add this as GitHub secret AWS_DEV_ROLE_ARN" -ForegroundColor Green
