# LLM Configuration System - Deployment Guide

**Version**: 1.0.0  
**Last Updated**: October 30, 2025  
**Target Environment**: AWS (DynamoDB, S3, ElastiCache)

---

## Overview

This guide covers deployment of the LLM Configuration System to AWS infrastructure, including database setup, S3 configuration, caching, and API deployment.

---

## Prerequisites

### AWS Services Required

- **DynamoDB**: Configuration and template storage
- **S3**: Template content storage
- **ElastiCache (Redis)**: Caching layer
- **IAM**: Service roles and permissions
- **CloudWatch**: Logging and monitoring
- **Secrets Manager**: API keys and credentials

### Tools Required

- AWS CLI v2.x
- Python 3.11+
- Terraform or CloudFormation (optional)
- Docker (for local testing)

---

## Infrastructure Setup

### 1. DynamoDB Tables

#### Configuration Table

Create the LLM configuration table:

```bash
aws dynamodb create-table \
  --table-name llm-configurations-${ENVIRONMENT} \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    "IndexName=GSI1,\
     KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],\
     Projection={ProjectionType=ALL},\
     ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Environment,Value=${ENVIRONMENT} Key=Service,Value=LLMConfig
```

**Enable Point-in-Time Recovery**:

```bash
aws dynamodb update-continuous-backups \
  --table-name llm-configurations-${ENVIRONMENT} \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

**Enable Encryption**:

```bash
aws dynamodb update-table \
  --table-name llm-configurations-${ENVIRONMENT} \
  --sse-specification Enabled=true,SSEType=KMS
```

#### Template Table

Create the template metadata table:

```bash
aws dynamodb create-table \
  --table-name llm-templates-${ENVIRONMENT} \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    "IndexName=GSI1,\
     KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],\
     Projection={ProjectionType=ALL},\
     ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Environment,Value=${ENVIRONMENT} Key=Service,Value=LLMConfig
```

### 2. S3 Bucket

Create S3 bucket for template storage:

```bash
aws s3 mb s3://purpose-path-templates-${ENVIRONMENT} \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket purpose-path-templates-${ENVIRONMENT} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket purpose-path-templates-${ENVIRONMENT} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket purpose-path-templates-${ENVIRONMENT} \
  --lifecycle-configuration file://s3-lifecycle.json
```

**s3-lifecycle.json**:

```json
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

### 3. ElastiCache (Redis)

Create Redis cluster for caching:

```bash
aws elasticache create-replication-group \
  --replication-group-id llm-config-cache-${ENVIRONMENT} \
  --replication-group-description "LLM Config Cache" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token ${REDIS_AUTH_TOKEN} \
  --tags Key=Environment,Value=${ENVIRONMENT}
```

### 4. IAM Roles and Policies

Create service role:

```bash
aws iam create-role \
  --role-name LLMConfigServiceRole-${ENVIRONMENT} \
  --assume-role-policy-document file://trust-policy.json
```

**trust-policy.json**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Attach policies:

```bash
# DynamoDB access
aws iam put-role-policy \
  --role-name LLMConfigServiceRole-${ENVIRONMENT} \
  --policy-name DynamoDBAccess \
  --policy-document file://dynamodb-policy.json

# S3 access  
aws iam put-role-policy \
  --role-name LLMConfigServiceRole-${ENVIRONMENT} \
  --policy-name S3Access \
  --policy-document file://s3-policy.json

# ElastiCache access
aws iam put-role-policy \
  --role-name LLMConfigServiceRole-${ENVIRONMENT} \
  --policy-name ElastiCacheAccess \
  --policy-document file://elasticache-policy.json
```

---

## Application Deployment

### Environment Variables

Configure the following environment variables:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012

# DynamoDB Tables
export DYNAMODB_CONFIGURATION_TABLE=llm-configurations-${ENVIRONMENT}
export DYNAMODB_TEMPLATE_TABLE=llm-templates-${ENVIRONMENT}

# S3 Configuration
export S3_TEMPLATE_BUCKET=purpose-path-templates-${ENVIRONMENT}

# Redis Configuration
export REDIS_HOST=llm-config-cache-${ENVIRONMENT}.xxx.cache.amazonaws.com
export REDIS_PORT=6379
export REDIS_AUTH_TOKEN=${REDIS_AUTH_TOKEN}
export REDIS_SSL=true

# Cache TTLs (seconds)
export CACHE_CONFIG_TTL=900
export CACHE_TEMPLATE_TTL=1800

# Application
export ENVIRONMENT=${ENVIRONMENT}
export LOG_LEVEL=INFO
export API_VERSION=v1
```

### Docker Deployment

Build and deploy Docker image:

```bash
# Build image
docker build -t llm-config-service:${VERSION} .

# Tag for ECR
docker tag llm-config-service:${VERSION} \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/llm-config-service:${VERSION}

# Push to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/llm-config-service:${VERSION}
```

### ECS Task Definition

Create ECS task definition:

```json
{
  "family": "llm-config-service",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/LLMConfigServiceRole-${ENVIRONMENT}",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "llm-config-api",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/llm-config-service:${VERSION}",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "${ENVIRONMENT}"},
        {"name": "AWS_REGION", "value": "${AWS_REGION}"},
        {"name": "DYNAMODB_CONFIGURATION_TABLE", "value": "llm-configurations-${ENVIRONMENT}"},
        {"name": "DYNAMODB_TEMPLATE_TABLE", "value": "llm-templates-${ENVIRONMENT}"},
        {"name": "S3_TEMPLATE_BUCKET", "value": "purpose-path-templates-${ENVIRONMENT}"},
        {"name": "REDIS_HOST", "value": "${REDIS_HOST}"},
        {"name": "REDIS_PORT", "value": "6379"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "REDIS_AUTH_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:llm-config/redis-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/llm-config-service",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

---

## Database Initialization

### Seed Data

Initialize registries and default configurations:

```python
# Run seed script
python scripts/seed_llm_config.py --environment ${ENVIRONMENT}
```

**Seed Script Contents**:

1. Load interaction registry
2. Load model registry  
3. Create default configurations for each interaction
4. Upload default templates to S3
5. Create template metadata records

---

## Monitoring and Alerting

### CloudWatch Dashboards

Create monitoring dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name LLMConfigService-${ENVIRONMENT} \
  --dashboard-body file://cloudwatch-dashboard.json
```

### CloudWatch Alarms

Key alarms to configure:

1. **High Error Rate**:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name llm-config-high-error-rate-${ENVIRONMENT} \
  --alarm-description "High error rate in LLM Config Service" \
  --metric-name Errors \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

2. **High Latency**:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name llm-config-high-latency-${ENVIRONMENT} \
  --alarm-description "High latency in LLM Config Service" \
  --metric-name Latency \
  --namespace AWS/ApiGateway \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold
```

3. **Low Cache Hit Rate**:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name llm-config-low-cache-hit-rate-${ENVIRONMENT} \
  --alarm-description "Low cache hit rate" \
  --metric-name CacheHitRate \
  --namespace LLMConfig \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 90 \
  --comparison-operator LessThanThreshold
```

---

## Backup and Disaster Recovery

### DynamoDB Backups

Enable automatic backups:

```bash
# Point-in-time recovery (enabled during table creation)

# On-demand backup
aws dynamodb create-backup \
  --table-name llm-configurations-${ENVIRONMENT} \
  --backup-name llm-configs-manual-backup-$(date +%Y%m%d)

aws dynamodb create-backup \
  --table-name llm-templates-${ENVIRONMENT} \
  --backup-name llm-templates-manual-backup-$(date +%Y%m%d)
```

### S3 Backups

S3 versioning provides automatic backup. For cross-region replication:

```bash
aws s3api put-bucket-replication \
  --bucket purpose-path-templates-${ENVIRONMENT} \
  --replication-configuration file://replication-config.json
```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour

**Recovery Steps**:

1. Restore DynamoDB tables from backup
2. Restore S3 bucket from versioning
3. Rebuild ElastiCache cluster
4. Redeploy application containers
5. Run health checks and validation

---

## Security Hardening

### Network Security

1. **VPC Configuration**:
   - Private subnets for ECS tasks
   - NAT Gateway for outbound access
   - Security groups restricting access

2. **API Gateway**:
   - WAF rules for rate limiting
   - IP whitelisting for admin endpoints
   - Request validation

### Data Security

1. **Encryption at Rest**:
   - DynamoDB: KMS encryption
   - S3: AES-256 encryption
   - ElastiCache: At-rest encryption

2. **Encryption in Transit**:
   - TLS 1.3 for all API traffic
   - Redis TLS connection

### Access Control

1. **IAM Policies**: Least-privilege access
2. **API Authentication**: JWT tokens
3. **Audit Logging**: CloudTrail enabled

---

## Performance Optimization

### DynamoDB

1. **Read/Write Capacity**: Start with on-demand, monitor and switch to provisioned if cost-effective
2. **GSI Optimization**: Ensure efficient query patterns
3. **TTL**: Enable TTL for temporary data

### ElastiCache

1. **Instance Sizing**: Start with t3.micro, scale based on metrics
2. **Connection Pooling**: Reuse connections
3. **Eviction Policy**: Configure `allkeys-lru`

### S3

1. **CloudFront**: Add CDN for high-traffic templates
2. **Transfer Acceleration**: Enable for global access
3. **Intelligent Tiering**: For cost optimization

---

## Health Checks

### Application Health Endpoint

```http
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "dynamodb": "healthy",
    "s3": "healthy",
    "redis": "healthy"
  }
}
```

### Readiness Probe

```http
GET /ready

Response: 200 OK (ready) or 503 Service Unavailable (not ready)
```

---

## Rollback Procedure

If deployment fails:

1. **Immediate Rollback**:

```bash
aws ecs update-service \
  --cluster llm-config-cluster \
  --service llm-config-service \
  --task-definition llm-config-service:${PREVIOUS_VERSION}
```

2. **Verify Rollback**:

```bash
# Check service status
aws ecs describe-services \
  --cluster llm-config-cluster \
  --services llm-config-service

# Run health checks
curl https://api.purposepath.com/health
```

3. **Database Rollback** (if schema changed):

```bash
# Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name llm-configurations-${ENVIRONMENT} \
  --backup-arn ${BACKUP_ARN}
```

---

## Post-Deployment Validation

Run validation checklist:

- [ ] Health check endpoint returns 200
- [ ] DynamoDB tables accessible
- [ ] S3 bucket accessible
- [ ] Redis cache responding
- [ ] API endpoints return expected responses
- [ ] Authentication working
- [ ] CloudWatch logs flowing
- [ ] Metrics being recorded
- [ ] Alarms configured and active

---

## Troubleshooting

### Common Issues

**Issue**: Configuration not found

- Check DynamoDB table has data
- Verify GSI is active
- Check cache invalidation

**Issue**: Template rendering fails

- Verify S3 bucket permissions
- Check template syntax
- Validate required parameters

**Issue**: High latency

- Check Redis connection
- Monitor DynamoDB throttling
- Review S3 access patterns

**Issue**: Cache misses

- Verify Redis connectivity
- Check TTL configuration
- Monitor eviction rate

---

## Related Documentation

- [Architecture Overview](./LLM_CONFIGURATION_SYSTEM.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Operations Runbook](../operations/RUNBOOK.md)
