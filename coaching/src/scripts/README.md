# Coaching Topics Seed Scripts

Scripts for seeding coaching topics to the DynamoDB topics table.

## Overview

These scripts seed coaching topics into the `purposepath-topics-{env}` DynamoDB table.

## Scripts

### `seed_topics.py`
Main seeding script that:
- Creates all coaching topics in DynamoDB from the endpoint registry
- Supports 44 topics total
- Is idempotent (safe to run multiple times)
- Can update existing topics or skip them

## Usage

```bash
# Set environment variables
export AWS_PROFILE=purposepath-dev
export AWS_REGION=us-east-1
export STAGE=dev

# Run seed script
cd coaching
python -m src.scripts.seed_topics

# Run with options
python -m src.scripts.seed_topics --force-update  # Update existing
python -m src.scripts.seed_topics --dry-run       # Preview changes
python -m src.scripts.seed_topics --validate-only # Validate only
```

## Prerequisites

1. **Infrastructure Deployed**: DynamoDB topics table must exist
2. **AWS Credentials**: Configure AWS profile or credentials
3. **Dependencies**: Install Python dependencies
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
