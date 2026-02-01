# Parameter Store Configuration Guide

This guide explains how to manage runtime configuration using AWS Systems Manager Parameter Store.

## Overview

The PurposePath AI system uses AWS Parameter Store to store runtime-configurable settings that need to be updated without code deployments. This is particularly useful for:

- Default LLM model codes (as models change frequently)
- Feature flags
- Environment-specific configuration

**Infrastructure as Code:** Parameter Store values are defined in Pulumi infrastructure (`coaching/pulumi/__main__.py`) and automatically created/updated during deployment. No manual seeding required.

## Default Model Configuration

### Parameter Structure

Default model codes are stored in Parameter Store at:

```
/purposepath/{stage}/models/default_basic    - Model for Free/Basic tier topics
/purposepath/{stage}/models/default_premium  - Model for Premium/Ultimate tier topics
```

Where `{stage}` is `dev`, `staging`, or `prod`.

### Infrastructure Definition

Parameters are defined in Pulumi infrastructure and automatically created during `pulumi up`:

```python
# coaching/pulumi/__main__.py
default_models = {
    "dev": {
        "basic": "CLAUDE_3_5_SONNET_V2",
        "premium": "CLAUDE_OPUS_4_5",
    },
    "staging": {...},
    "prod": {...},
}
```

To change default values:
1. Edit `coaching/pulumi/__main__.py`
2. Run `pulumi up` to apply changes
3. Parameters are updated automatically

### Manual Seeding (Optional)

The seeding script is available for one-off updates without Pulumi deployment:

```bash
# Update specific models without deploying infrastructure
cd coaching
uv run python -m src.scripts.seed_parameter_store \
  --stage dev \
  --basic-model CLAUDE_3_7_SONNET \
  --premium-model CLAUDE_OPUS_4_5 \
  --force
```

**Note:** Manual updates will be overwritten on next `pulumi up` unless infrastructure code is also updated.

### Changing Default Models in Infrastructure

To change default model codes permanently:

1. **Edit Pulumi configuration:**
   ```python
   # coaching/pulumi/__main__.py
   default_models = {
       "prod": {
           "basic": "CLAUDE_3_7_SONNET",  # Changed
           "premium": "CLAUDE_OPUS_4_5",
       },
   }
   ```

2. **Deploy changes:**
   ```bash
   cd coaching/pulumi
   pulumi up
   ```

3. **Verify update:**
   ```bash
   aws ssm get-parameter \
     --name "/purposepath/prod/models/default_basic" \
     --region us-east-1
   ```

### Updating via AWS CLI

```bash
# Update basic model
aws ssm put-parameter \
  --name "/purposepath/dev/models/default_basic" \
  --value "CLAUDE_3_5_SONNET_V2" \
  --type "String" \
  --overwrite \
  --region us-east-1

# Update premium model
aws ssm put-parameter \
  --name "/purposepath/dev/models/default_premium" \
  --value "CLAUDE_OPUS_4_5" \
  --type "String" \
  --overwrite \
  --region us-east-1
```

### Updating via Admin API

Use the Admin API endpoints to update defaults programmatically:

```bash
# Get current default models
curl https://api.dev.purposepath.app/admin/system/default-models \
  -H "Authorization: Bearer $JWT_TOKEN"

# Update default models
curl -X PUT https://api.dev.purposepath.app/admin/system/default-models \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "basic_model_code": "CLAUDE_3_5_SONNET_V2",
    "premium_model_code": "CLAUDE_OPUS_4_5"
  }'

# List available model codes
curl https://api.dev.purposepath.app/admin/system/available-models \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Verifying Current Values

```bash
# Get basic model
aws ssm get-parameter \
  --name "/purposepath/dev/models/default_basic" \
  --region us-east-1

# Get premium model
aws ssm get-parameter \
  --name "/purposepath/dev/models/default_premium" \
  --region us-east-1

# Get both with details
aws ssm get-parameters \
  --names \
    "/purposepath/dev/models/default_basic" \
    "/purposepath/dev/models/default_premium" \
  --with-decryption \
  --region us-east-1
```

## Valid Model Codes

Model codes must exist in `MODEL_REGISTRY` (`coaching/src/core/llm_models.py`).

Common valid codes:
- `CLAUDE_3_5_SONNET_V2` - Claude 3.5 Sonnet v2 (October 2024)
- `CLAUDE_SONNET_4_5` - Claude Sonnet 4.5 (September 2025)
- `CLAUDE_OPUS_4_5` - Claude Opus 4.5 (November 2025)
- `CLAUDE_3_7_SONNET` - Claude 3.7 Sonnet (February 2025)
- `GPT_4O` - GPT-4o
- `GPT_5_MINI` - GPT-5 Mini

Use the Admin API `/admin/system/available-models` endpoint to get the full list with capabilities and pricing.

## How It Works

### Runtime Flow

1. When a new topic is auto-created from registry:
   - System checks Parameter Store for default models
   - If found, uses those values
   - If not found or error, falls back to hardcoded defaults
   - Values are cached for 5 minutes for performance

2. When admin updates defaults via API:
   - New values written to Parameter Store
   - Cache is cleared
   - Next topic creation uses new values immediately

### Caching Behavior

- **Cache TTL**: 5 minutes
- **Cache per Lambda**: Each Lambda instance has its own cache
- **Cache invalidation**: Automatic on update via API or `clear_cache()` method
- **Cold start**: No cache, fetches fresh from Parameter Store

### Fallback Strategy

```
1. Try Parameter Store (cached for 5 min)
   ↓ (if fails)
2. Use hardcoded defaults in code
   - basic_model_code: "CLAUDE_3_5_SONNET_V2"
   - premium_model_code: "CLAUDE_OPUS_4_5"
```

This ensures the system always has valid model codes even if Parameter Store is unavailable.

## Deployment Checklist

After deploying Pulumi infrastructure:

- [ ] **Verify parameters** were created:
  ```bash
  aws ssm get-parameters \
    --names "/purposepath/dev/models/default_basic" "/purposepath/dev/models/default_premium" \
    --region us-east-1
  ```

- [ ] **Verify via Pulumi outputs**:
  ```bash
  cd coaching/pulumi
  pulumi stack output defaultBasicModelParam
  pulumi stack output defaultPremiumModelParam
  ```

**Note:** IAM permissions and parameter creation are handled automatically by Pulumi. No manual steps required.

## Monitoring

### CloudWatch Logs

Watch for Parameter Store errors:

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/purposepath-coaching-api-dev \
  --filter-pattern "Parameter Store" \
  --start-time $(($(date -u +%s) - 3600))000
```

### Key Log Messages

- `"Parameter Store service initialized"` - Service created successfully
- `"Loaded default models from Parameter Store"` - Cache miss, fetched from SSM
- `"Using hardcoded fallback default models"` - Parameter Store unavailable, using fallback
- `"Default models updated in Parameter Store"` - Admin updated defaults via API

## Troubleshooting

### Issue: "No default model parameters found"

**Cause:** Parameters not seeded in Parameter Store

**Solution:**
```bash
uv run python -m coaching.src.scripts.seed_parameter_store --stage {env}
```

### Issue: "AccessDeniedException" from Parameter Store

**Cause:** Lambda IAM role lacks SSM permissions

**Solution:** Add SSM permissions to Lambda execution role (see Deployment Checklist above)

### Issue: Old models still being used after update

**Cause:** Lambda cache hasn't expired yet

**Solution:** Wait 5 minutes for cache to expire, or trigger cold start by updating Lambda environment variable

## Cost

**Parameter Store Standard Tier: $0.00/month**

- 10,000 parameters max (we use 2)
- 40 TPS throughput (more than sufficient)
- No storage or API call charges
- No additional AWS costs

## Related Files

- `coaching/src/services/parameter_store_service.py` - Parameter Store service
- `coaching/src/scripts/seed_parameter_store.py` - Seeding script
- `coaching/src/api/routes/admin/system_config.py` - Admin API endpoints
- `coaching/src/core/topic_seed_data.py` - Uses Parameter Store defaults
- `coaching/src/domain/entities/llm_topic.py` - Uses Parameter Store defaults

---

**Last Updated:** 2026-02-01  
**Related Issues:** #208
