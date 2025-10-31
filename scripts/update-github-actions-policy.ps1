#!/usr/bin/env pwsh
# Update IAM policy for github-actions-deploy user

$PolicyDocument = Get-Content -Path "$PSScriptRoot\..\docs\GITHUB_ACTIONS_IAM_POLICY.json" -Raw

Write-Host "Updating IAM policy for github-actions-deploy user..." -ForegroundColor Cyan

aws iam put-user-policy `
    --user-name github-actions-deploy `
    --policy-name GitHubActionsDeployPolicy `
    --policy-document $PolicyDocument

if ($LASTEXITCODE -eq 0) {
    Write-Host "Policy updated successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to update policy" -ForegroundColor Red
    exit 1
}
