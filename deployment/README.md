# PurposePath Deployment Architecture

## Overview

This deployment architecture solves the "update nightmare" by separating shared infrastructure from service-specific resources. The architecture consists of:

1. **Shared Infrastructure** - One-time deployment of common resources
2. **Service Templates** - Lightweight Lambda-only templates that reference shared resources
3. **Unified Deployment Scripts** - Automated deployment with dependency management

## Architecture Benefits

✅ **Eliminates Update Nightmares** - Shared resources are deployed once and rarely changed  
✅ **Preserves Existing Infrastructure** - Custom domains, certificates, and databases remain intact  
✅ **Enables Runtime Switching** - Deploy Python or .NET to same infrastructure seamlessly  
✅ **Simplifies Maintenance** - Service deployments are fast and focused  
✅ **Ensures Consistency** - All services use same VPC, databases, and configuration  

## Directory Structure

```
deployment/
├── shared-infrastructure/
│   ├── template.yaml                    # All shared AWS resources
│   └── deploy-shared-infrastructure.ps1 # One-time deployment script
└── account-service/
    └── template-dotnet.yaml            # .NET Lambda template (legacy)

# Current streamlined structure:
account/
└── template.yaml                       # Streamlined .NET Lambda template
deploy-account.ps1                      # Single deployment script
```

## Shared Infrastructure Components

The `shared-infrastructure/template.yaml` includes:

### Networking & Security
- **VPC** with public/private subnets
- **NAT Gateway** for Lambda internet access
- **Security Groups** for Lambda and Redis
- **VPC Endpoints** for DynamoDB and S3 (cost optimization)

### Storage & Caching
- **DynamoDB Tables** (Users, Tokens, Tenants, Sessions, etc.)
- **ElastiCache Redis** cluster for session management
- **S3 Buckets** for application data and logs

### Authentication & Secrets
- **JWT Secret** in AWS Secrets Manager (auto-generated or imported)
- **IAM Policies** and permissions for services

### Custom Domain & SSL
- **Route53 DNS** records
- **SSL Certificates** via AWS Certificate Manager
- **API Gateway Custom Domain** with proper routing

### Monitoring & Observability
- **CloudWatch Dashboard** with key metrics
- **CloudWatch Alarms** for error monitoring

## Service Templates

Both `template-dotnet.yaml` and `template-python.yaml` are lightweight and include only:

- **Lambda Function** with runtime-specific configuration
- **API Gateway** for the service
- **API Routes** and event mappings
- **Custom Domain Mapping** to shared domain
- **IAM Policies** referencing shared resources via ImportValue

## Deployment Process

### 1. Deploy Shared Infrastructure (One-time)

```powershell
cd deployment/shared-infrastructure
.\deploy-shared-infrastructure.ps1 -Stage dev -HostedZoneId Z123456789ABCDEF
```

**Parameters:**
- `Stage` - dev, staging, or prod
- `HostedZoneId` - Route53 zone for custom domain (optional)
- `JwtSecretArn` - Existing JWT secret (optional, will create if not provided)
- `RedisNodeType` - ElastiCache instance type
- `EmailFrom` - SES sender email

### 2. Deploy Account Service

```powershell
.\deploy-account.ps1 -Stage dev
```

**Parameters:**
- `Stage` - deployment stage (default: dev)

**Note**: Current implementation deploys .NET Lambda using existing shared DynamoDB tables from `purposepath-api-dev` stack.

## Key Features

### Automatic Dependency Management
The service deployment script automatically:
- ✅ Checks for shared infrastructure
- ✅ Offers to deploy it if missing
- ✅ Validates all required exports exist
- ✅ Builds and tests the service
- ✅ Deploys with proper configuration

### Resource Import/Export Pattern
Shared resources are exported with consistent naming:
```yaml
# Shared template exports
Outputs:
  UsersTableName:
    Value: !Ref UsersTable
    Export:
      Name: !Sub purposepath-users-table-${Stage}
```

Service templates import via `Fn::ImportValue`:
```yaml
# Service template imports
Environment:
  Variables:
    USERS_TABLE: 
      Fn::ImportValue: !Sub purposepath-users-table-${Stage}
```

### Custom Domain Configuration
The architecture uses existing custom domain:
- **Domain:** `api.dev.purposepath.app`
- **SSL Certificate:** Managed by ACM (existing)
- **API Mappings:**
  - `/account/*` → .NET Account Service
  - `/coaching/*` → Python Coaching Service  
  - `/traction/*` → Python Traction Service
- **Shared Infrastructure:** Uses existing DynamoDB tables and JWT secrets

## Migration from Existing Infrastructure

To migrate from existing deployments:

1. **Deploy Shared Infrastructure** (preserves existing resources)
2. **Deploy New Service** using either runtime
3. **Update Domain Mapping** to point to new API Gateway
4. **Verify Endpoints** work correctly
5. **Delete Old Stack** once satisfied

## Current Deployment Status

**Active Services:**
- ✅ .NET Account Service: `purposepath-account-dotnet-dev`
- ✅ Python Coaching Service: `purposepath-coaching-api-dev`
- ✅ Python Traction Service: `purposepath-traction-api-dev`
- ✅ Shared Infrastructure: `purposepath-api-dev` (DynamoDB tables, JWT secrets)
- ✅ Custom Domain: `purposepath-api-domain-dev`

**Deployment Command:**
```powershell
.\deploy-account.ps1 -Stage dev
```

## Monitoring & Troubleshooting

### CloudWatch Resources
- **Dashboard:** `purposepath-dashboard-dev`
- **Log Groups:** `/aws/lambda/purposepath-account-api-dev`
- **Metrics:** Lambda errors, duration, throttles
- **Alarms:** Automatic notifications on issues

### Troubleshooting Commands
```powershell
# Check shared infrastructure status
aws cloudformation describe-stacks --stack-name purposepath-shared-infrastructure-dev

# List available exports
aws cloudformation list-exports | grep purposepath

# Check service deployment
aws cloudformation describe-stacks --stack-name purposepath-account-api-dev

# View recent logs
aws logs tail /aws/lambda/purposepath-account-api-dev --follow
```

## Security Considerations

- **VPC Isolation** - Lambdas run in private subnets
- **Secrets Management** - JWT secrets stored in AWS Secrets Manager
- **IAM Least Privilege** - Minimal permissions for each service
- **Encryption** - Redis and S3 encryption enabled in production
- **Network Security** - Security groups restrict access

## Cost Optimization

- **VPC Endpoints** - Reduce NAT Gateway usage for AWS services
- **On-Demand DynamoDB** - Pay per request pricing
- **Shared Resources** - Multiple services share VPC, Redis, etc.
- **Efficient Lambda** - Right-sized memory and timeout settings

This architecture provides a robust, scalable, and maintainable deployment solution that eliminates infrastructure drift while preserving existing resources and enabling seamless runtime migrations.