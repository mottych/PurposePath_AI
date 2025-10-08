#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy PurposePath shared infrastructure (one-time deployment)

.DESCRIPTION
Deploys the shared AWS infrastructure including VPC, DynamoDB tables, ElastiCache Redis, 
S3 buckets, custom domains, certificates, and CloudWatch resources. This should be 
deployed once and rarely updated.

.PARAMETER Stage
The deployment stage (dev, staging, prod)

.PARAMETER HostedZoneId
Route53 Hosted Zone ID for custom domain (required for domain creation)

.PARAMETER JwtSecretArn
Existing JWT Secret ARN (optional - will create new if not provided)

.PARAMETER RedisNodeType
ElastiCache Redis node type

.PARAMETER SkipConfirmation
Skip confirmation prompts

.EXAMPLE
.\deploy-shared-infrastructure.ps1 -Stage dev -HostedZoneId Z123456789ABCDEF

.EXAMPLE
.\deploy-shared-infrastructure.ps1 -Stage dev -HostedZoneId Z123456789ABCDEF -JwtSecretArn "arn:aws:secretsmanager:us-east-1:123456789:secret:jwt-abc123"
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Stage,
    
    [Parameter(Mandatory = $false)]
    [string]$HostedZoneId = "",
    
    [Parameter(Mandatory = $false)]
    [string]$JwtSecretArn = "",
    
    [Parameter(Mandatory = $false)]
    [ValidateSet("cache.t3.micro", "cache.t3.small", "cache.t3.medium")]
    [string]$RedisNodeType = "cache.t3.micro",
    
    [Parameter(Mandatory = $false)]
    [string]$EmailFrom = "noreply@purposepath.ai",
    
    [Parameter(Mandatory = $false)]
    [string]$DomainName = "api.dev.purposepath.app",
    
    [switch]$SkipConfirmation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$script:Green = "`e[32m"
$script:Yellow = "`e[33m"
$script:Red = "`e[31m"
$script:Blue = "`e[34m"
$script:Reset = "`e[0m"

function Write-Info {
    param([string]$Message)
    Write-Host "${Blue}[INFO]${Reset} $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}[SUCCESS]${Reset} $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${Yellow}[WARNING]${Reset} $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "${Red}[ERROR]${Reset} $Message"
}

function Test-AWSCredentials {
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Info "AWS Identity: $($identity.Arn)"
        return $true
    }
    catch {
        Write-Error "AWS credentials not configured or invalid"
        Write-Info "Run 'aws configure' to set up your credentials"
        return $false
    }
}

function Test-SAMInstalled {
    try {
        $samVersion = sam --version
        Write-Info "SAM CLI Version: $samVersion"
        return $true
    }
    catch {
        Write-Error "AWS SAM CLI not installed or not in PATH"
        Write-Info "Install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
        return $false
    }
}

function Get-StackStatus {
    param([string]$StackName)
    
    try {
        $stack = aws cloudformation describe-stacks --stack-name $StackName --output json 2>$null | ConvertFrom-Json
        return $stack.Stacks[0].StackStatus
    }
    catch {
        return $null
    }
}

function Wait-ForStackCompletion {
    param(
        [string]$StackName,
        [string]$Operation
    )
    
    Write-Info "Waiting for $Operation to complete..."
    
    do {
        Start-Sleep -Seconds 15
        $status = Get-StackStatus -StackName $StackName
        Write-Info "Stack status: $status"
        
        if ($status -like "*_COMPLETE") {
            if ($status -like "*_FAILED" -or $status -eq "ROLLBACK_COMPLETE") {
                throw "Stack $Operation failed with status: $status"
            }
            break
        }
        elseif ($status -like "*_FAILED") {
            throw "Stack $Operation failed with status: $status"
        }
    } while ($status -like "*_IN_PROGRESS")
}

# Main deployment function
function Deploy-SharedInfrastructure {
    Write-Info "Starting PurposePath Shared Infrastructure deployment..."
    Write-Info "Stage: $Stage"
    Write-Info "Domain: $DomainName"
    Write-Info "Redis Node Type: $RedisNodeType"
    
    if ($HostedZoneId) {
        Write-Info "Hosted Zone ID: $HostedZoneId (custom domain will be created)"
    } else {
        Write-Warning "No Hosted Zone ID provided - custom domain will be skipped"
    }
    
    if ($JwtSecretArn) {
        Write-Info "Using existing JWT Secret: $JwtSecretArn"
    } else {
        Write-Info "JWT Secret will be created automatically"
    }
    
    # Confirmation
    if (-not $SkipConfirmation) {
        Write-Warning "This will deploy shared infrastructure for stage '$Stage'"
        Write-Warning "This includes VPC, DynamoDB tables, Redis cluster, S3 buckets, and custom domain"
        $confirmation = Read-Host "Are you sure you want to continue? (y/N)"
        if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
            Write-Info "Deployment cancelled by user"
            return
        }
    }
    
    # Check if stack already exists
    $stackName = "purposepath-shared-infrastructure-$Stage"
    $existingStatus = Get-StackStatus -StackName $stackName
    
    if ($existingStatus) {
        Write-Warning "Stack '$stackName' already exists with status: $existingStatus"
        if (-not $SkipConfirmation) {
            $update = Read-Host "Do you want to update the existing stack? (y/N)"
            if ($update -ne 'y' -and $update -ne 'Y') {
                Write-Info "Deployment cancelled by user"
                return
            }
        }
    }
    
    # Build parameters
    $parameters = @(
        "Stage=$Stage",
        "RedisNodeType=$RedisNodeType",
        "EmailFrom=$EmailFrom",
        "DomainName=$DomainName"
    )
    
    if ($HostedZoneId) {
        $parameters += "HostedZoneId=$HostedZoneId"
    }
    
    if ($JwtSecretArn) {
        $parameters += "JwtSecretArn=$JwtSecretArn"
    }
    
    $parameterOverrides = $parameters -join " "
    
    try {
        Write-Info "Validating SAM template..."
        sam validate --template-file template.yaml
        Write-Success "Template validation passed"
        
        Write-Info "Deploying shared infrastructure..."
        Write-Info "Parameters: $parameterOverrides"
        
        # Deploy with SAM
        $deployCommand = @(
            "sam", "deploy",
            "--template-file", "template.yaml",
            "--stack-name", $stackName,
            "--capabilities", "CAPABILITY_IAM",
            "--parameter-overrides", $parameterOverrides,
            "--no-fail-on-empty-changeset",
            "--no-confirm-changeset"
        )
        
        Write-Info "Executing: $($deployCommand -join ' ')"
        & $deployCommand[0] $deployCommand[1..($deployCommand.Length-1)]
        
        if ($LASTEXITCODE -ne 0) {
            throw "SAM deployment failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "Shared infrastructure deployment completed successfully!"
        
        # Display stack outputs
        Write-Info "Retrieving stack outputs..."
        $outputs = aws cloudformation describe-stacks --stack-name $stackName --query "Stacks[0].Outputs" --output table
        Write-Info "Stack Outputs:"
        Write-Host $outputs
        
        Write-Success "Shared infrastructure is ready for service deployments"
        Write-Info "You can now deploy account and coaching services using their respective templates"
        
    } catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        
        # Show recent stack events for troubleshooting
        Write-Info "Recent stack events:"
        try {
            $events = aws cloudformation describe-stack-events --stack-name $stackName --max-items 10 --output table
            Write-Host $events
        } catch {
            Write-Warning "Could not retrieve stack events"
        }
        
        throw
    }
}

# Main script execution
try {
    Write-Info "PurposePath Shared Infrastructure Deployment"
    Write-Info "==========================================="
    
    # Validate prerequisites
    if (-not (Test-AWSCredentials)) {
        exit 1
    }
    
    if (-not (Test-SAMInstalled)) {
        exit 1
    }
    
    # Change to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    Write-Info "Working directory: $((Get-Location).Path)"
    
    # Validate template exists
    if (-not (Test-Path "template.yaml")) {
        Write-Error "template.yaml not found in current directory"
        exit 1
    }
    
    # Execute deployment
    Deploy-SharedInfrastructure
    
} catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    exit 1
}