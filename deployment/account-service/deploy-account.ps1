#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy PurposePath Account Service

.DESCRIPTION
Deploys the PurposePath Account Service Lambda function using either Python or .NET runtime.
The deployment uses runtime-specific templates that reference shared infrastructure.
Automatically checks for and optionally deploys shared infrastructure if not present.

.PARAMETER Runtime
The runtime to deploy (python or dotnet)

.PARAMETER Stage
The deployment stage (dev, staging, prod)

.PARAMETER SkipTests
Skip running tests before deployment

.PARAMETER SkipBuild
Skip building the application before deployment

.PARAMETER SkipSharedInfraCheck
Skip checking for shared infrastructure (assume it exists)

.EXAMPLE
.\deploy-account.ps1 -Runtime dotnet -Stage dev

.EXAMPLE
.\deploy-account.ps1 -Runtime python -Stage dev -SkipTests
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("python", "dotnet")]
    [string]$Runtime,
    
    [Parameter(Mandatory = $false)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Stage = "dev",
    
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [switch]$SkipSharedInfraCheck,
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

function Test-Prerequisites {
    # Test AWS credentials
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Info "AWS Identity: $($identity.Arn)"
    }
    catch {
        Write-Error "AWS credentials not configured or invalid"
        return $false
    }
    
    # Test SAM CLI
    try {
        $samVersion = sam --version
        Write-Info "SAM CLI Version: $samVersion"
    }
    catch {
        Write-Error "AWS SAM CLI not installed or not in PATH"
        return $false
    }
    
    return $true
}

function Test-SharedInfrastructure {
    param([string]$Stage)
    
    $stackName = "purposepath-shared-infrastructure-$Stage"
    
    try {
        $stack = aws cloudformation describe-stacks --stack-name $stackName --output json 2>$null | ConvertFrom-Json
        $status = $stack.Stacks[0].StackStatus
        
        if ($status -eq "CREATE_COMPLETE" -or $status -eq "UPDATE_COMPLETE") {
            Write-Success "Shared infrastructure stack '$stackName' is available"
            
            # Verify key exports exist
            $exports = aws cloudformation list-exports --output json | ConvertFrom-Json
            $requiredExports = @(
                "purposepath-users-table-$Stage",
                "purposepath-jwt-secret-arn-$Stage",
                "purposepath-domain-name-$Stage"
            )
            
            $missingExports = @()
            foreach ($exportName in $requiredExports) {
                $found = $exports.Exports | Where-Object { $_.Name -eq $exportName }
                if (-not $found) {
                    $missingExports += $exportName
                }
            }
            
            if ($missingExports.Count -gt 0) {
                Write-Warning "Missing required exports: $($missingExports -join ', ')"
                return $false
            }
            
            return $true
        } else {
            Write-Warning "Shared infrastructure stack '$stackName' exists but status is: $status"
            return $false
        }
    }
    catch {
        Write-Warning "Shared infrastructure stack '$stackName' not found"
        return $false
    }
}

function Deploy-SharedInfrastructureIfNeeded {
    param([string]$Stage)
    
    if (-not (Test-SharedInfrastructure -Stage $Stage)) {
        Write-Info "Shared infrastructure not ready for stage '$Stage'"
        
        if (-not $SkipConfirmation) {
            $deployShared = Read-Host "Would you like to deploy shared infrastructure now? (y/N)"
            if ($deployShared -ne 'y' -and $deployShared -ne 'Y') {
                Write-Error "Shared infrastructure is required for service deployment"
                Write-Info "Run the following command first:"
                Write-Info "  cd ..\shared-infrastructure"
                Write-Info "  .\deploy-shared-infrastructure.ps1 -Stage $Stage -HostedZoneId <your-zone-id>"
                return $false
            }
        }
        
        Write-Info "Deploying shared infrastructure..."
        $sharedInfraPath = Join-Path $PSScriptRoot "..\shared-infrastructure"
        
        if (-not (Test-Path $sharedInfraPath)) {
            Write-Error "Shared infrastructure directory not found: $sharedInfraPath"
            Write-Info "Expected path: $((Resolve-Path $sharedInfraPath -ErrorAction SilentlyContinue))"
            return $false
        }
        
        Push-Location $sharedInfraPath
        try {
            # Deploy with minimal configuration for service deployment
            # Note: This may fail without HostedZoneId for custom domain
            .\deploy-shared-infrastructure.ps1 -Stage $Stage -SkipConfirmation
            
            if ($LASTEXITCODE -ne 0) {
                throw "Shared infrastructure deployment failed"
            }
        }
        finally {
            Pop-Location
        }
    }
    
    return $true
}

function Build-DotNetService {
    Write-Info "Building .NET Account Service..."
    
    $servicePath = "..\..\pp_api\Services\PurposePath.Account.Lambda"
    
    if (-not (Test-Path $servicePath)) {
        Write-Error ".NET service path not found: $servicePath"
        Write-Info "Expected path: $((Resolve-Path $servicePath -ErrorAction SilentlyContinue))"
        return $false
    }
    
    Push-Location $servicePath
    try {
        Write-Info "Restoring NuGet packages..."
        dotnet restore
        
        if ($LASTEXITCODE -ne 0) {
            throw "Package restore failed"
        }
        
        Write-Info "Building project..."
        dotnet build --configuration Release --no-restore
        
        if ($LASTEXITCODE -ne 0) {
            throw "Build failed"
        }
        
        Write-Success ".NET build completed successfully"
        return $true
    }
    finally {
        Pop-Location
    }
}

function Test-DotNetService {
    Write-Info "Running .NET tests..."
    
    $testPath = "..\..\pp_api"
    
    if (-not (Test-Path $testPath)) {
        Write-Warning ".NET project path not found: $testPath - skipping tests"
        return $true
    }
    
    Push-Location $testPath
    try {
        dotnet test --configuration Release --no-build --verbosity normal
        
        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed"
        }
        
        Write-Success ".NET tests passed"
        return $true
    }
    finally {
        Pop-Location
    }
}

function Test-PythonService {
    Write-Info "Running Python tests..."
    
    $pythonPath = "..\..\pp_ai_submodule\account"
    
    if (-not (Test-Path $pythonPath)) {
        Write-Warning "Python service path not found: $pythonPath - skipping tests"
        return $true
    }
    
    Push-Location $pythonPath
    try {
        # Check if pytest is available
        python -m pytest --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            python -m pytest tests/ -v
            
            if ($LASTEXITCODE -ne 0) {
                throw "Python tests failed"
            }
            
            Write-Success "Python tests passed"
        } else {
            Write-Warning "pytest not available - skipping Python tests"
        }
        
        return $true
    }
    finally {
        Pop-Location
    }
}

function Deploy-AccountService {
    param(
        [string]$Runtime,
        [string]$Stage
    )
    
    $templateFile = "template-$Runtime.yaml"
    $stackName = "purposepath-account-api-$Stage"
    
    Write-Info "Deploying Account Service ($Runtime runtime)..."
    Write-Info "Template: $templateFile"
    Write-Info "Stack: $stackName"
    Write-Info "Stage: $Stage"
    
    # Validate template
    Write-Info "Validating SAM template..."
    sam validate --template-file $templateFile
    
    if ($LASTEXITCODE -ne 0) {
        throw "Template validation failed"
    }
    
    Write-Success "Template validation passed"
    
    # Build parameters
    $parameters = @(
        "Stage=$Stage"
    )
    
    if ($Runtime -eq "dotnet") {
        $parameters += "LogLevel=Information"
    } else {
        $parameters += "LogLevel=INFO"
    }
    
    $parameterOverrides = $parameters -join " "
    
    # Deploy
    Write-Info "Deploying with parameters: $parameterOverrides"
    
    sam deploy `
        --template-file $templateFile `
        --stack-name $stackName `
        --capabilities CAPABILITY_IAM `
        --parameter-overrides $parameterOverrides `
        --no-fail-on-empty-changeset `
        --no-confirm-changeset
    
    if ($LASTEXITCODE -ne 0) {
        throw "Deployment failed"
    }
    
    Write-Success "Account Service deployment completed successfully!"
    
    # Display outputs
    Write-Info "Retrieving stack outputs..."
    try {
        $outputs = aws cloudformation describe-stacks --stack-name $stackName --query "Stacks[0].Outputs" --output table
        Write-Info "Stack Outputs:"
        Write-Host $outputs
        
        # Show API endpoint
        $endpoint = aws cloudformation describe-stacks --stack-name $stackName --query "Stacks[0].Outputs[?OutputKey=='AccountHttpApiEndpoint'].OutputValue" --output text
        if ($endpoint) {
            Write-Success "API Endpoint: $endpoint"
        }
        
        # Show custom domain if available
        try {
            $domainName = aws cloudformation list-exports --query "Exports[?Name=='purposepath-domain-name-$Stage'].Value" --output text
            if ($domainName -and $domainName -ne "None") {
                Write-Success "Custom Domain: https://$domainName/account"
            }
        } catch {
            # Ignore errors getting domain name
        }
        
    } catch {
        Write-Warning "Could not retrieve stack outputs"
    }
}

# Main script execution
try {
    Write-Info "PurposePath Account Service Deployment"
    Write-Info "======================================"
    Write-Info "Runtime: $Runtime"
    Write-Info "Stage: $Stage"
    
    # Change to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    Write-Info "Working directory: $((Get-Location).Path)"
    
    # Validate prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # Ensure shared infrastructure is deployed (unless skipped)
    if (-not $SkipSharedInfraCheck) {
        if (-not (Deploy-SharedInfrastructureIfNeeded -Stage $Stage)) {
            exit 1
        }
    } else {
        Write-Warning "Skipping shared infrastructure check - assuming it exists"
    }
    
    # Build if needed
    if (-not $SkipBuild) {
        if ($Runtime -eq "dotnet") {
            if (-not (Build-DotNetService)) {
                exit 1
            }
        } else {
            Write-Info "Python service - no build step required"
        }
    } else {
        Write-Warning "Skipping build step"
    }
    
    # Run tests if needed
    if (-not $SkipTests) {
        if ($Runtime -eq "dotnet") {
            if (-not (Test-DotNetService)) {
                exit 1
            }
        } else {
            if (-not (Test-PythonService)) {
                exit 1
            }
        }
    } else {
        Write-Warning "Skipping tests"
    }
    
    # Validate template exists
    $templateFile = "template-$Runtime.yaml"
    if (-not (Test-Path $templateFile)) {
        Write-Error "Template file not found: $templateFile"
        Write-Info "Available files: $((Get-ChildItem -Name '*.yaml').Name -join ', ')"
        exit 1
    }
    
    # Final confirmation
    if (-not $SkipConfirmation) {
        Write-Warning "This will deploy the Account Service ($Runtime) to stage '$Stage'"
        Write-Info "This will replace any existing Account Service deployment in this stage"
        $confirmation = Read-Host "Are you sure you want to continue? (y/N)"
        if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
            Write-Info "Deployment cancelled by user"
            exit 0
        }
    }
    
    # Deploy the service
    Deploy-AccountService -Runtime $Runtime -Stage $Stage
    
    Write-Success "Account Service ($Runtime) deployment completed successfully!"
    
    Write-Info ""
    Write-Info "Next steps:"
    Write-Info "- Test the API endpoints"
    Write-Info "- Update custom domain mapping if needed"
    Write-Info "- Monitor CloudWatch logs for any issues"
    
} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    
    # Show some troubleshooting info
    Write-Info ""
    Write-Info "Troubleshooting:"
    Write-Info "- Check AWS credentials and permissions"
    Write-Info "- Verify shared infrastructure is deployed"
    Write-Info "- Check SAM CLI logs for detailed error information"
    Write-Info "- Ensure all required resources are available in the target region"
    
    exit 1
}