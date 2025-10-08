# Amazon Q Developer - PurposePath .NET Account Service Deployment

## Situation Overview

I need to deploy a .NET 8 Lambda account service to replace an existing Python Lambda, using existing AWS infrastructure while preserving all current resources and the custom domain `api.dev.purposepath.app`.

## Current Infrastructure State

### Existing CloudFormation Stacks:
- `purposepath-account-api-dev` - Python account service (currently running)
- `purposepath-coaching-api-dev` - Python coaching service  
- `purposepath-api-domain-dev` - Custom domain configuration
- `purposepath-api-domain-mapping-dev` - Domain mappings

### Current API Endpoints (Working):
- **Python API**: `https://0p2vat7dn0.execute-api.us-east-1.amazonaws.com/api/v1/auth/health`
- **Custom Domain**: `https://api.dev.purposepath.app` (should route to account service)
- **Expected .NET endpoint after deployment**: Same endpoints but served by .NET Lambda

### Existing CloudFormation Exports:
```
purposepath-api-endpoint-dev
purposepath-business-data-table-dev  
purposepath-coaching-sessions-table-dev
purposepath-conversations-table-dev
purposepath-jwt-secret-arn-dev
purposepath-redis-endpoint-dev
purposepath-subscriptions-table-dev
purposepath-tenants-table-dev
purposepath-users-table-dev
purposepath-vpc-id-dev
```

## Deployment Goal

Deploy a .NET 8 Lambda account service that:
1. **Replaces** the existing Python account service
2. **Preserves** all existing infrastructure (VPC, DynamoDB tables, Redis, custom domain)
3. **Maintains** the same API endpoints and custom domain routing
4. **Uses** existing shared resources via CloudFormation imports
5. **Creates** only the missing DynamoDB tables needed by the account service

## Key Requirements

### Must Preserve:
- ✅ Custom domain: `api.dev.purposepath.app`
- ✅ Existing DynamoDB tables (Users, Tenants, etc.)
- ✅ JWT secret in AWS Secrets Manager
- ✅ Redis cluster for session management
- ✅ VPC and networking configuration
- ✅ API Gateway domain mappings

### Must Deploy:
- 🔄 .NET 8 Lambda function (replacing Python)
- 🔄 API Gateway HTTP API for .NET service
- 🔄 Missing DynamoDB tables (RefreshTokens, PasswordResets, VerificationTokens, UserPreferences)
- 🔄 Proper IAM roles and policies
- 🔄 Domain mapping to route traffic to new .NET API

## Technical Details

### .NET Application Structure:
```
pp_api/Services/PurposePath.Account.Lambda/
├── LambdaEntryPoint.cs           # AWS Lambda entry point
├── Startup.cs                    # ASP.NET Core startup
├── PurposePath.Account.Lambda.csproj
└── (other application files)
```

### Handler Configuration:
- **Runtime**: dotnet8
- **Handler**: `PurposePath.Account.Lambda::PurposePath.Account.Lambda.LambdaEntryPoint::FunctionHandlerAsync`
- **Timeout**: 30 seconds
- **Memory**: 512 MB

### Environment Variables Needed:
```
USERS_TABLE: (import from existing)
TENANTS_TABLE: (import from existing) 
SUBSCRIPTIONS_TABLE: (import from existing)
REFRESH_TOKENS_TABLE: (create new)
PASSWORD_RESETS_TABLE: (create new)
VERIFICATION_TOKENS_TABLE: (create new)
USER_PREFERENCES_TABLE: (create new)
JWT_SECRET_ARN: (import from existing)
```

## Deployment Challenges Encountered

### Issue 1: Export Name Conflicts
- Our new template exports conflict with existing stack exports
- Need unique export names or avoid conflicts entirely

### Issue 2: Missing Table Structure
- Some DynamoDB tables exist in shared infrastructure
- Others need to be created in the account service stack
- Need proper import/create strategy

### Issue 3: Domain Mapping Complexity  
- Custom domain mappings need to be updated to point to new API Gateway
- Must preserve existing SSL certificates and Route53 configuration

### Issue 4: Stack Dependencies
- Existing Python stack might need to be deleted carefully
- Risk of breaking shared resources if not handled properly

## Documentation References

### 1. Main Project README
**Location**: `/README.md`
**Key Sections**:
- Repository structure explanation
- Deployment architecture overview  
- Services configuration
- Git workflow for monorepo

### 2. Deployment Architecture Guide
**Location**: `/deployment/README.md`
**Key Sections**:
- Shared infrastructure pattern explanation
- Service template structure
- Runtime switching capabilities
- Import/Export pattern for CloudFormation
- Custom domain preservation strategy
- Troubleshooting commands

### 3. .NET API Documentation  
**Location**: `/pp_api/README.md`
**Key Sections**:
- Architecture overview (Clean Architecture/DDD)
- Required configuration settings
- AWS deployment configuration
- Environment variables structure

### 4. Python Services Reference
**Location**: `/pp_ai/README.md`
**Key Sections**:
- Current Python service structure
- Shared types system
- Integration with .NET services

## Current Template Files

### 1. .NET Service Template
**Location**: `/deployment/account-service/template-dotnet.yaml`
**Status**: Modified to use existing exports, needs validation

### 2. Deployment Script
**Location**: `/deployment/account-service/deploy-account.ps1`
**Features**: Automatic dependency checking, validation, deployment

### 3. Shared Infrastructure Template (New)
**Location**: `/deployment/shared-infrastructure/template.yaml`
**Status**: Created but conflicts with existing infrastructure

## Specific Ask for Amazon Q

Please provide a deployment strategy that:

### 1. **Analysis Phase**
- Review the existing CloudFormation exports and stack structure
- Identify which resources should be imported vs created
- Determine the safest migration path from Python to .NET

### 2. **Template Strategy** 
- Should I modify existing stacks or create new ones?
- How to handle the export name conflicts?
- Best approach for DynamoDB table management (import vs create)

### 3. **Migration Approach**
- Can I do a blue/green deployment preserving the custom domain?
- Should I delete the Python stack first or deploy alongside?
- How to ensure zero downtime during the switch?

### 4. **Domain Mapping Strategy**
- How to update API Gateway domain mappings safely?
- Preserve SSL certificates and Route53 configuration
- Ensure `/account/api/v1/*` routes to the new .NET Lambda

### 5. **Validation Steps**
- How to test the deployment before switching traffic?
- Recommended health checks and validation endpoints
- Rollback strategy if issues occur

## Expected Deliverables

1. **Corrected CloudFormation template** for .NET service
2. **Step-by-step deployment commands** with proper sequencing
3. **Validation script** to test the deployment
4. **Rollback procedure** if needed
5. **Custom domain verification** commands

## Additional Context

- **AWS Region**: us-east-1
- **Stage**: dev (development environment)
- **Domain**: api.dev.purposepath.app
- **Current Working Python API**: https://0p2vat7dn0.execute-api.us-east-1.amazonaws.com/api/v1/auth/health

The goal is a seamless migration that preserves all existing functionality while moving from Python to .NET runtime, using AWS best practices for infrastructure management and zero-downtime deployments.