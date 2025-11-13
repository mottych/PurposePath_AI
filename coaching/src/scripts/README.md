# Coaching Topics Seed Scripts

Scripts for migrating coaching topics from the old hardcoded enum to the new unified DynamoDB table structure.

## Overview

These scripts are part of the unified prompt management system migration. They seed the 4 coaching topics (Core Values, Purpose, Vision, Goals) into the `purposepath-llm-prompts-{env}` DynamoDB table and migrate existing prompts from the old YAML format to the new markdown format.

## Scripts

### 1. `seed_coaching_topics.py`
Main seeding script that:
- Creates all 4 coaching topics in DynamoDB
- Migrates existing prompts from `prompts/{topic}/latest.yaml` to `prompts/{topic_id}/{type}.md`
- Is idempotent (safe to run multiple times)
- Skips topics that already exist

### 2. `verify_coaching_topics.py`
Verification script that:
- Checks all 4 topics exist in DynamoDB
- Validates topic configuration
- Reports missing or misconfigured topics

## Usage

### Option 1: Shell Scripts (Recommended)

```bash
# Seed topics to dev environment
./scripts/seed_topics_manual.sh dev

# Verify seeding
./scripts/verify_topics.sh dev

# For other environments
./scripts/seed_topics_manual.sh staging
./scripts/verify_topics.sh staging
```

### Option 2: Direct Python Execution

```bash
# Set environment variables
export AWS_PROFILE=purposepath-dev
export LLM_PROMPTS_TABLE=purposepath-llm-prompts-dev
export PROMPTS_BUCKET=purposepath-coaching-prompts-dev
export AWS_REGION=us-east-1
export STAGE=dev

# Run seed script
cd coaching
python -m src.scripts.seed_coaching_topics

# Run verification
python -m src.scripts.verify_coaching_topics
```

## Prerequisites

1. **Infrastructure Deployed**: DynamoDB table and S3 bucket must exist
2. **AWS Credentials**: Configure AWS profile or credentials
3. **Dependencies**: Install Python dependencies (`pip install -r requirements.txt`)

## Topics Seeded

| Topic ID | Topic Name | Type | Category | Prompts |
|----------|------------|------|----------|---------|
| core_values | Core Values Discovery | conversation_coaching | coaching | system, user |
| purpose | Life Purpose Exploration | conversation_coaching | coaching | system, user |
| vision | Vision Statement Creation | conversation_coaching | coaching | system, user |
| goals | Goal Setting & Planning | conversation_coaching | coaching | system, user |

## Configuration

Each topic includes:
- **Metadata**: Name, description, display order
- **Type**: `conversation_coaching`
- **Category**: `coaching`
- **Parameters**: user_name, user_id, conversation_history
- **LLM Config**: Model, temperature, streaming settings
- **Prompts**: System and user prompts (migrated from YAML if available)

## Prompt Migration

### Old Format (YAML)
```
prompts/core_values/latest.yaml
```
Contains both system_prompt and user_prompt_template in single file.

### New Format (Markdown)
```
prompts/core_values/system.md
prompts/core_values/user.md
```
Separate files for each prompt type, stored as markdown.

**Migration Behavior:**
- If old YAML exists: Automatically migrates to new format
- If old YAML missing: Topic created without prompts (admin must add via API)
- Old YAML files remain untouched (cleaned up later)

## Idempotency

The seed script is **idempotent**:
- ✅ Safe to run multiple times
- ✅ Skips existing topics
- ✅ Does not overwrite data
- ✅ Reports what was created vs skipped

## Troubleshooting

### "Topic already exists, skipping"
This is normal if you've run the script before. The script won't overwrite existing topics.

### "No existing prompts found for migration"
This means no old YAML file exists in S3. Admin must create prompts via the API endpoints.

### DynamoDB Access Denied
Ensure your AWS credentials have DynamoDB PutItem permission for the table.

### S3 Access Denied
Ensure your AWS credentials have S3 GetObject and PutObject permissions for the bucket.

## Verification

After seeding, verify with:

```bash
# Check DynamoDB table
aws dynamodb scan \
  --table-name purposepath-llm-prompts-dev \
  --index-name topic_type-index \
  --expression-attribute-values '{":type":{"S":"conversation_coaching"}}' \
  --filter-expression "topic_type = :type"

# Check S3 prompts
aws s3 ls s3://purposepath-coaching-prompts-dev/prompts/ --recursive

# Or use verification script
./scripts/verify_topics.sh dev
```

## Next Steps

After seeding:
1. **Verify**: Run verification script
2. **Test**: Test conversation endpoints work with new topics
3. **Create Prompts**: If no prompts were migrated, create them via admin API
4. **Deploy**: Topics are now ready for use

## Related Issues

- #78: Infrastructure setup
- #79: Domain models and repository
- #80: Admin API endpoints
- #81: Service layer migration
- #82: This seed script (final epic task)

## Notes

- Seed script should be run **once per environment** after infrastructure deployment
- The CoachingTopic enum remains for backward compatibility
- Old YAML prompts can be removed in a future cleanup issue
- Prompts can be updated via the admin API after seeding
