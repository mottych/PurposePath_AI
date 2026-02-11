# Issue #208 Resolution Summary

## Problem

The `strategy_suggestions` topic was failing with:
```
ValidationException: The provided model identifier is invalid
```

## Root Cause

Two separate issues were discovered:

### 1. Invalid Claude Opus 4.5 Model ID (Immediate Bug)
- **Configured in DynamoDB**: `CLAUDE_OPUS_4_5` (for premium tier)
- **MODEL_REGISTRY mapping**: `anthropic.claude-opus-4-5-20250929-v1:0` ❌
- **Actual Bedrock model**: `anthropic.claude-opus-4-5-20251101-v1:0` ✅

The MODEL_REGISTRY had the wrong release date (September 29 instead of November 1).

### 2. Hardcoded Invalid Defaults (Future-proofing Issue)
- Default models in seed data were hardcoded invalid values
- No way to update defaults without code deployment
- As models change frequently, this would cause recurring issues

## Solutions Implemented

### Fix 1: Correct Claude Opus 4.5 Model ID

**Files Updated:**
- `coaching/src/core/llm_models.py` - MODEL_REGISTRY
- `coaching/src/infrastructure/llm/bedrock_provider.py` - Model lists

**Commit:** `fix(#208): correct Claude Opus 4.5 model ID date`

### Fix 2: Runtime-Configurable Default Models

**New Components:**

1. **Parameter Store Service** (`coaching/src/services/parameter_store_service.py`)
   - Reads default model codes from AWS SSM Parameter Store
   - 5-minute cache for performance
   - Automatic fallback to hardcoded defaults

2. **Admin API Endpoints** (`coaching/src/api/routes/admin/system_config.py`)
   - `GET /admin/system/default-models` - View current defaults
   - `PUT /admin/system/default-models` - Update defaults (admin only)
   - `GET /admin/system/available-models` - List valid model codes

3. **Seeding Script** (`coaching/src/scripts/seed_parameter_store.py`)
   - Initializes Parameter Store with default values
   - Supports dry-run mode
   - Environment-specific configuration

4. **Updated Logic**
   - `topic_seed_data.py` - Loads defaults from Parameter Store
   - `llm_topic.py` - Uses Parameter Store for auto-created topics

**Commit:** `feat(#208): make default model codes configurable via Parameter Store`

## Benefits

✅ **No code deployments** when models change  
✅ **Runtime updates** via Admin API or AWS CLI  
✅ **Per-environment configuration** (different models in dev/prod)  
✅ **Free** (AWS Parameter Store Standard tier)  
✅ **Safe fallback** if Parameter Store unavailable  
✅ **Admin UI ready** (API endpoints implemented)  

## Post-Deployment Steps

### 1. Deploy Pulumi Infrastructure

Parameter Store values are now managed by Pulumi infrastructure:

```bash
cd coaching/pulumi
pulumi up  # Creates/updates SSM parameters automatically
```

Parameters are defined in `coaching/pulumi/__main__.py`:
```python
default_models = {
    "dev": {
        "basic": "CLAUDE_3_5_SONNET_V2",
        "premium": "CLAUDE_OPUS_4_5",
    },
    ...
}
```

### 2. Verify Parameters Created

```bash
# Via AWS CLI
aws ssm get-parameters \
  --names \
    "/purposepath/dev/models/default_basic" \
    "/purposepath/dev/models/default_premium" \
  --region us-east-1

# Or via Pulumi outputs
cd coaching/pulumi
pulumi stack output defaultBasicModelParam
pulumi stack output defaultPremiumModelParam
```

**Note:** IAM permissions are automatically granted by Pulumi. No manual configuration needed.

## Usage Examples

### Update Defaults via Infrastructure (Recommended)

```python
# 1. Edit coaching/pulumi/__main__.py
default_models = {
    "prod": {
        "basic": "CLAUDE_3_7_SONNET",
        "premium": "CLAUDE_OPUS_4_5",
    },
}

# 2. Deploy changes
cd coaching/pulumi
pulumi up
```

### Update Defaults via API (Runtime)

```bash
curl -X PUT https://api.dev.purposepath.app/admin/system/default-models \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "basic_model_code": "CLAUDE_3_7_SONNET",
    "premium_model_code": "CLAUDE_OPUS_4_5"
  }'
```

**Note:** Runtime API updates will be overwritten on next `pulumi up` unless infrastructure code is also updated.

### Update via AWS CLI (One-off)

```bash
aws ssm put-parameter \
  --name "/purposepath/dev/models/default_basic" \
  --value "CLAUDE_3_7_SONNET" \
  --type "String" \
  --overwrite \
  --region us-east-1
```

**Note:** CLI updates will be overwritten on next `pulumi up` unless infrastructure code is also updated.

## Testing

Strategy suggestions topic should now work:
1. For basic tier users → Uses Claude Sonnet 4.5
2. For premium tier users → Uses Claude Opus 4.5 (now with correct model ID)

## Documentation

- **Configuration Guide**: `docs/operations/PARAMETER_STORE_CONFIGURATION.md`
- **Deployment Checklist**: `docs/operations/POST_DEPLOYMENT_CHECKLIST.md` (updated)

## Status

✅ **Fixed and merged to dev**  
✅ **Documentation complete**  
✅ **Tests passing**  
🚀 **Ready for deployment**

---

**Issue:** #208  
**Resolution Date:** February 1, 2026  
**Commits:**
- `07c9698` - fix(#208): correct Claude Opus 4.5 model ID date
- `e1b49b4` - feat(#208): make default model codes configurable via Parameter Store
- `d7a95e1` - docs: add Parameter Store configuration guide
