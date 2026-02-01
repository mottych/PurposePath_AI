# Post-Deployment Checklist

This checklist ensures all required post-deployment steps are completed after deploying the PurposePath AI services.

## 🎯 Overview

After deploying infrastructure and services, several manual steps must be completed to ensure the system is fully operational. This document covers those critical steps.

---

## ✅ 1. Verify Infrastructure Deployment

Before proceeding, ensure all infrastructure is deployed successfully:

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name purposepath-api-{env}

# Verify DynamoDB tables exist
aws dynamodb list-tables | grep purposepath
```

**Required Tables:**
- `purposepath-topics-{env}` - Topic definitions
- `purposepath-users-{env}` - User accounts
- `purposepath-tenants-{env}` - Tenant data
- `purposepath-sessions-{env}` - Session data
- `purposepath-ai-jobs-{env}` - Async AI jobs

---

## ✅ 2. Seed Parameter Store Defaults

**⚠️ NEW STEP** - Initialize default model configuration in Parameter Store.

### Why This is Needed

Default model codes for topic creation are stored in AWS Parameter Store, allowing runtime updates without code deployments. This step initializes the parameters.

### Seeding Command

```bash
# Seed Parameter Store defaults
cd coaching
uv run python -m src.scripts.seed_parameter_store --stage {env}

# Example for production with specific models
uv run python -m src.scripts.seed_parameter_store \
  --stage prod \
  --basic-model CLAUDE_3_5_SONNET_V2 \
  --premium-model CLAUDE_OPUS_4_5 \
  --force
```

### Verification

```bash
aws ssm get-parameters \
  --names \
    "/purposepath/{env}/models/default_basic" \
    "/purposepath/{env}/models/default_premium" \
  --region us-east-1
```

---

## ✅ 3. Seed AI Topics to DynamoDB

**⚠️ CRITICAL STEP** - This step is **required** for AI functionality to work.

### Why This is Needed

AI topics are defined in code (`topic_registry.py`) but must be seeded into DynamoDB for the runtime engine to access them. Missing this step will cause "Topic not found or inactive" errors.

### Seeding Commands

#### Seed All Topics (First Deployment)

```bash
# Set AWS credentials
export AWS_PROFILE=purposepath-{env}
export AWS_REGION=us-east-1
export STAGE={env}  # dev, staging, or prod

# Seed all topics
cd coaching
uv run python -m src.scripts.seed_topics
```

#### Seed Specific Topic (After Code Changes)

```bash
# Seed a single topic with force update
uv run python -m src.scripts.seed_topics \
  --topic-id alignment_check \
  --force-update
```

#### Validate Topics

```bash
# Check which topics are missing or need updates
uv run python -m src.scripts.seed_topics --validate-only
```

### Topics to Seed

The system currently has **44+ topics** across multiple categories:

- **Onboarding** - website_scan, onboarding_suggestions, niche_review, ica_review, value_proposition_review, core_values, purpose, vision
- **Strategic Planning** - strategy_suggestions, measure_recommendations, alignment_check, alignment_explanation, alignment_suggestions
- **Operations** - root_cause_suggestions, action_suggestions, optimize_action_plan, prioritization_suggestions, scheduling_suggestions
- **Analysis** - alignment_analysis, measure_analysis, operations_analysis
- **Insights** - insights_generation

### Verification

After seeding, verify topics were created:

```bash
# Check DynamoDB
aws dynamodb scan \
  --table-name purposepath-topics-{env} \
  --max-items 5

# Check specific topic
aws dynamodb get-item \
  --table-name purposepath-topics-{env} \
  --key '{"topic_id": {"S": "alignment_check"}}'

# Check S3 prompts
aws s3 ls s3://purposepath-coaching-prompts-{env}/prompts/alignment_check/
```

**Expected Output:**
- Topic records in DynamoDB with `is_active: true`
- Prompt files in S3 (`system.md`, `user.md`)

---

## ✅ 4. Test AI Endpoints

After seeding Parameter Store and topics, test key endpoints:

### Health Check

```bash
curl https://api.{env}.purposepath.app/health
```

**Expected:** `{"status": "healthy"}`

### Test Alignment Check Topic

```bash
curl -X POST https://api.{env}.purposepath.app/ai/execute-async \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topicId": "alignment_check",
    "parameters": {
      "goal_id": "test-goal-123"
    }
  }'
```

**Expected:** Job ID returned, no "Topic not found" error

---

## ✅ 5. Verify Custom Domain & SSL

```bash
# Test custom domain
curl -I https://api.{env}.purposepath.app/health

# Check SSL certificate
openssl s_client -connect api.{env}.purposepath.app:443 -servername api.{env}.purposepath.app
```

**Expected:**
- HTTP 200 response
- Valid SSL certificate
- Correct domain routing

---

## ✅ 6. Check CloudWatch Logs

Monitor initial traffic and errors:

```bash
# Tail recent logs
aws logs tail /aws/lambda/purposepath-coaching-api-{env} --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/purposepath-coaching-api-{env} \
  --filter-pattern "ERROR"
```

---

## ✅ 7. Verify ElastiCache Redis

```bash
# Check Redis cluster
aws elasticache describe-cache-clusters \
  --cache-cluster-id purposepath-redis-{env}

# Test connectivity (from Lambda or EC2 in same VPC)
redis-cli -h {redis-endpoint} ping
```

**Expected:** `PONG` response

---

## ✅ 8. Update Documentation

- [ ] Update API documentation with new endpoints
- [ ] Update environment variables documentation
- [ ] Document any new configuration requirements
- [ ] Update team wiki/runbooks

---

## 🚨 Common Issues & Solutions

### Issue: "Topic not found or inactive"

**Root Cause:** Topics not seeded to DynamoDB

**Solution:**
```bash
cd coaching
uv run python -m src.scripts.seed_topics --topic-id {topic_id} --force-update
```

### Issue: "NoSuchBucket" error when seeding

**Root Cause:** S3 prompts bucket doesn't exist

**Solution:**
1. Verify infrastructure deployment completed
2. Check bucket name matches environment:
   ```bash
   aws s3 ls | grep purposepath-coaching-prompts
   ```
3. Re-run infrastructure deployment if missing

### Issue: "Access Denied" when seeding

**Root Cause:** AWS credentials lack DynamoDB/S3 permissions

**Solution:**
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Check IAM permissions for DynamoDB PutItem and S3 PutObject
3. Use correct AWS profile: `export AWS_PROFILE=purposepath-{env}`

---

## 📋 Environment-Specific Checklists

### Development

- [ ] Infrastructure deployed
- [ ] Topics seeded (all 44 topics)
- [ ] Test endpoints working
- [ ] Logs accessible

### Staging

- [ ] Infrastructure deployed
- [ ] Topics seeded (all 44 topics)
- [ ] Test endpoints working
- [ ] SSL certificate valid
- [ ] Smoke tests passing

### Production

- [ ] Infrastructure deployed
- [ ] **Topics seeded (all 44 topics)** ⚠️ CRITICAL
- [ ] Test endpoints working
- [ ] SSL certificate valid
- [ ] Monitoring/alarms configured
- [ ] Backup verification
- [ ] Smoke tests passing
- [ ] Load testing completed
- [ ] Rollback plan documented

---

## 🔄 Updating Existing Deployments

When adding new topics or updating existing ones:

1. **Code Changes:**
   - Update `topic_registry.py` with new/modified topic definitions
   - Update `topic_seed_data.py` with prompt templates
   - Commit and deploy code

2. **Database Update:**
   ```bash
   # Force update topics in DynamoDB
   uv run python -m src.scripts.seed_topics --force-update
   ```

3. **Verification:**
   ```bash
   # Validate all topics
   uv run python -m src.scripts.seed_topics --validate-only
   ```

---

## 📝 Notes

- **Topic seeding is NOT automated** in CI/CD pipeline (by design)
- Seeding is **idempotent** - safe to run multiple times
- Use `--force-update` to overwrite existing topics
- Use `--dry-run` to preview changes without applying
- Keep this checklist updated as deployment process evolves

---

## 🆘 Support

If you encounter issues:

1. Check CloudWatch logs for detailed errors
2. Verify AWS credentials and permissions
3. Review this checklist for missed steps
4. Contact DevOps team or create GitHub issue

---

**Last Updated:** 2026-01-30  
**Maintained By:** DevOps Team
