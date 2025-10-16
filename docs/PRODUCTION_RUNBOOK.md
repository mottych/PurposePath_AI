# Production Runbook - PurposePath AI Coaching

**Version:** 1.0.0  
**Last Updated:** October 16, 2025  
**Maintainer:** PurposePath Engineering Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Deployment](#deployment)
4. [Monitoring & Observability](#monitoring--observability)
5. [Common Operations](#common-operations)
6. [Troubleshooting](#troubleshooting)
7. [Incident Response](#incident-response)
8. [Rollback Procedures](#rollback-procedures)

---

## Overview

### Service Details

- **Service Name:** PurposePath AI Coaching
- **Tech Stack:** Python 3.11, FastAPI, AWS Lambda, DynamoDB
- **Deployment:** AWS SAM, GitHub Actions
- **Environments:** Dev, Staging, Production

### Key Dependencies

- **AWS Services:** Lambda, API Gateway, DynamoDB, Secrets Manager, CloudWatch, X-Ray
- **External APIs:** .NET Business API
- **LLM Providers:** Bedrock/OpenAI (configurable)

---

## Architecture

### High-Level Architecture

```
API Gateway → Lambda (FastAPI) → DynamoDB
                ↓
          Business API (External)
                ↓
          LLM Provider
```

### Key Components

- **API Layer:** FastAPI running on AWS Lambda via Mangum
- **Data Layer:** DynamoDB for conversation and template storage
- **Observability:** CloudWatch Logs, Metrics, X-Ray Tracing
- **Authentication:** JWT tokens validated via shared secret

---

## Deployment

### Automated Deployments

#### Development (Auto-deploy from `main`)

```bash
# Triggered automatically on push to main branch
# Manual trigger via GitHub Actions UI
```

#### Staging (Auto-deploy from `staging`)

```bash
# Triggered automatically on push to staging branch
# Manual trigger via GitHub Actions workflow_dispatch
```

#### Production (Auto-deploy from `main` with approval)

```bash
# Triggered automatically on push to main branch
# Requires environment protection rules approval
```

### Manual Deployment

```bash
# 1. Authenticate with AWS
aws sso login --profile purposepath-prod

# 2. Build SAM application
sam build --template coaching/template-standalone.yaml --parallel

# 3. Deploy to production
sam deploy \
  --template-file coaching/template-standalone.yaml \
  --stack-name purposepath-coaching-api-prod \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides Stage=prod LogLevel=WARNING \
  --region us-east-1 \
  --resolve-s3 \
  --guided

# 4. Verify deployment
aws cloudformation describe-stacks \
  --stack-name purposepath-coaching-api-prod \
  --query "Stacks[0].Outputs"
```

---

## Monitoring & Observability

### CloudWatch Dashboards

**Access:** AWS Console → CloudWatch → Dashboards

Key Dashboards:
- `PurposePath-Coaching-Overview` - Service health overview
- `PurposePath-Coaching-Performance` - Latency and throughput metrics
- `PurposePath-Coaching-Errors` - Error rates and types

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `APILatency` | API response time (P95) | > 2000ms |
| `ErrorRate` | Percentage of failed requests | > 1% |
| `LLM_TotalTokens` | Token usage per request | > 4000 tokens |
| `CacheMiss` | Cache miss rate | > 50% |
| `DynamoDB_ConsumedCapacity` | DynamoDB RCU/WCU usage | > 80% provisioned |

### CloudWatch Logs

**Log Groups:**
- `/aws/lambda/purposepath-coaching-api-prod`

**Query Examples:**

```
# Find errors in the last hour
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

# Track API latency
fields @timestamp, duration_ms, operation
| filter operation = "process_message"
| stats avg(duration_ms), max(duration_ms), pct(duration_ms, 95) by bin(5m)

# Monitor token usage
fields @timestamp, prompt_tokens, completion_tokens, total_tokens, model
| filter model like /gpt/
| stats sum(total_tokens), avg(total_tokens) by bin(1h)
```

### X-Ray Tracing

**Access:** AWS Console → X-Ray → Service Map

Key Views:
- Service map showing request flow
- Trace timeline for individual requests
- Error and fault analysis

---

## Common Operations

### Check Service Health

```bash
# Get API endpoint
API_URL=$(aws cloudformation describe-stacks \
  --stack-name purposepath-coaching-api-prod \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

# Health check
curl ${API_URL}/health
```

### View Recent Logs

```bash
# Tail logs (requires AWS CLI)
aws logs tail /aws/lambda/purposepath-coaching-api-prod \
  --follow \
  --format short

# Get logs from last 30 minutes
aws logs tail /aws/lambda/purposepath-coaching-api-prod \
  --since 30m \
  --format short
```

### Update Environment Variables

```bash
# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name purposepath-coaching-api-prod \
  --environment Variables={STAGE=prod,LOG_LEVEL=INFO}

# Verify update
aws lambda get-function-configuration \
  --function-name purposepath-coaching-api-prod \
  --query "Environment.Variables"
```

### Rotate Secrets

```bash
# Update JWT secret
aws secretsmanager update-secret \
  --secret-id purposepath/jwt-secret/prod \
  --secret-string "new-secret-value"

# Trigger Lambda deployment to pick up new secret
aws lambda update-function-configuration \
  --function-name purposepath-coaching-api-prod \
  --environment Variables={SECRET_ROTATION_ID=$(date +%s)}
```

---

## Troubleshooting

### High Latency

**Symptoms:** P95 latency > 2000ms

**Investigation:**
1. Check X-Ray traces for slow components
2. Review CloudWatch metrics for LLM latency
3. Check DynamoDB throttling metrics
4. Review cache hit rates

**Resolution:**
- Optimize DynamoDB queries
- Increase Lambda memory (improves CPU)
- Enable caching for repeated queries
- Review LLM prompt sizes

### High Error Rate

**Symptoms:** Error rate > 1%

**Investigation:**
1. Check CloudWatch Logs for error messages
2. Review X-Ray for failed subsegments
3. Check external API connectivity
4. Verify DynamoDB table status

**Resolution:**
- Fix code bugs (deploy hotfix)
- Verify external API availability
- Check IAM permissions
- Review rate limiting

### LLM Token Overuse

**Symptoms:** Token costs exceeding budget

**Investigation:**
1. Query CloudWatch for LLM token metrics
2. Review conversation lengths
3. Check prompt templates

**Resolution:**
- Implement conversation pruning
- Optimize prompt templates
- Add token limits per request
- Enable response streaming

### Database Throttling

**Symptoms:** DynamoDB throttled requests

**Investigation:**
1. Check CloudWatch metrics: `ConsumedReadCapacityUnits`, `ConsumedWriteCapacityUnits`
2. Review throttled request count
3. Check access patterns

**Resolution:**
- Enable auto-scaling
- Implement exponential backoff
- Optimize query patterns
- Consider on-demand capacity

---

## Incident Response

### Severity Levels

- **P0 (Critical):** Service completely down, impacting all users
- **P1 (High):** Major functionality broken, impacting >50% users
- **P2 (Medium):** Minor functionality broken, impacting <50% users
- **P3 (Low):** Cosmetic issues, no user impact

### Incident Response Process

1. **Detect** - Alerts or user reports
2. **Assess** - Determine severity and impact
3. **Mitigate** - Immediate action to restore service
4. **Resolve** - Permanent fix
5. **Review** - Post-mortem and prevention

### Emergency Contacts

- **On-Call Engineer:** [PagerDuty rotation]
- **Team Lead:** [Contact info]
- **AWS Support:** [Support plan link]

### Communication Channels

- **Slack:** `#purposepath-incidents`
- **Status Page:** [Status page URL]
- **Email:** incidents@purposepath.ai

---

## Rollback Procedures

### Automated Rollback (via CloudFormation)

```bash
# List recent stack updates
aws cloudformation describe-stack-events \
  --stack-name purposepath-coaching-api-prod \
  --max-items 20

# Cancel in-progress update
aws cloudformation cancel-update-stack \
  --stack-name purposepath-coaching-api-prod

# Rollback to previous version
aws cloudformation update-stack \
  --stack-name purposepath-coaching-api-prod \
  --use-previous-template \
  --parameters UsePreviousValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

### Manual Rollback (via Lambda Versions)

```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name purposepath-coaching-api-prod

# Get previous version ARN
PREVIOUS_VERSION=$(aws lambda list-versions-by-function \
  --function-name purposepath-coaching-api-prod \
  --query "Versions[-2].Version" \
  --output text)

# Update alias to previous version
aws lambda update-alias \
  --function-name purposepath-coaching-api-prod \
  --name live \
  --function-version $PREVIOUS_VERSION
```

### Verify Rollback

```bash
# Check API health
curl ${API_URL}/health

# Check recent logs
aws logs tail /aws/lambda/purposepath-coaching-api-prod \
  --since 5m \
  --format short

# Monitor error rates
# (Check CloudWatch dashboard)
```

---

## Additional Resources

- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Architecture Design](./Architecture/AI_COACHING_ARCHITECTURE_DESIGN.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [AWS Console](https://console.aws.amazon.com/)

---

**Note:** This runbook should be reviewed and updated quarterly to ensure accuracy.
