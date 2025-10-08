# PowerShell script to upload prompt templates to S3

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Stage,
    
    [string]$Region = "us-east-1",
    [string]$Topic = "",
    [switch]$DryRun
)

Write-Host "Uploading prompt templates to $Stage environment..." -ForegroundColor Green

# Check AWS CLI
if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Error "AWS CLI is not installed."
    exit 1
}

# Verify AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
}

$BucketName = "truenorth-coaching-prompts-$Stage"

# Create bucket if it doesn't exist
try {
    aws s3 ls "s3://$BucketName" | Out-Null
    Write-Host "S3 bucket $BucketName exists" -ForegroundColor Green
} catch {
    Write-Host "Creating S3 bucket $BucketName..." -ForegroundColor Yellow
    if (!$DryRun) {
        aws s3 mb "s3://$BucketName" --region $Region
    } else {
        Write-Host "[DRY RUN] Would create bucket: $BucketName" -ForegroundColor Cyan
    }
}

# Upload specific topic or all topics
if ($Topic) {
    $PromptPath = "prompts/$Topic/"
    $S3Path = "s3://$BucketName/prompts/$Topic/"
    
    if (!(Test-Path $PromptPath)) {
        Write-Error "Prompt directory not found: $PromptPath"
        exit 1
    }
    
    Write-Host "Uploading prompts for topic: $Topic" -ForegroundColor Yellow
} else {
    $PromptPath = "prompts/"
    $S3Path = "s3://$BucketName/prompts/"
    Write-Host "Uploading all prompt templates..." -ForegroundColor Yellow
}

# Sync files
if (!$DryRun) {
    aws s3 sync $PromptPath $S3Path --delete
    Write-Host "Prompt templates uploaded successfully!" -ForegroundColor Green
} else {
    Write-Host "[DRY RUN] Would sync: $PromptPath to $S3Path" -ForegroundColor Cyan
    aws s3 sync $PromptPath $S3Path --delete --dryrun
}

# List uploaded files
Write-Host "`nUploaded prompt templates:" -ForegroundColor Cyan
if ($Topic) {
    aws s3 ls "s3://$BucketName/prompts/$Topic/" --recursive
} else {
    aws s3 ls "s3://$BucketName/prompts/" --recursive
}