## ✅ Documentation Deployed Successfully

The post-deployment checklist and runbook have been deployed to the dev environment.

### 🎯 Action Required: Seed Topics in Deployed Environment

To resolve the "Topic not found or inactive" error, you must now **manually seed the topics** in the deployed environment. This is a one-time post-deployment step.

#### Quick Fix (Immediate)

```bash
# Connect to AWS
export AWS_PROFILE=purposepath-dev
export AWS_REGION=us-east-1
export STAGE=dev

# Seed alignment_check topic
cd coaching
uv run python -m src.scripts.seed_topics --topic-id alignment_check --force-update
```

#### Comprehensive Fix (Recommended)

Seed all 44 topics to prevent future occurrences:

```bash
# Seed all topics at once
cd coaching
uv run python -m src.scripts.seed_topics --force-update

# Validate
uv run python -m src.scripts.seed_topics --validate-only
```

#### Verification

After seeding, test the endpoint:

```bash
curl -X POST https://api.dev.purposepath.app/ai/execute-async \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topicId": "alignment_check",
    "parameters": {
      "goal_id": "test-goal-123"
    }
  }'
```

**Expected:** Job ID returned without "Topic not found" error.

### 📚 Documentation References

- **Post-Deployment Checklist:** `docs/operations/POST_DEPLOYMENT_CHECKLIST.md`
- **Runbook:** `docs/operations/RUNBOOK_TOPIC_NOT_FOUND.md`
- **Seeding Script:** `coaching/src/scripts/seed_topics.py`

### 🔄 For Other Environments

Repeat the seeding process for staging and production:

```bash
# Staging
export AWS_PROFILE=purposepath-staging
export STAGE=staging
cd coaching
uv run python -m src.scripts.seed_topics --force-update

# Production
export AWS_PROFILE=purposepath-prod
export STAGE=prod
cd coaching
uv run python -m src.scripts.seed_topics --force-update
```

---

**Status:** Documentation complete ✅  
**Next Step:** Seed topics in deployed environment (manual action required)  
**Closing issue** once seeding instructions are confirmed.
