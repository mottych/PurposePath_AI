"""PurposePath Infrastructure - DynamoDB Tables, S3, and Secrets Manager.

This Pulumi project manages the core infrastructure for the PurposePath AI platform:
- DynamoDB tables for coaching conversations and sessions
- S3 bucket for LLM prompts
- Secrets Manager for API keys (OpenAI, Google Vertex AI)

Tables are configured with on-demand billing, appropriate indexes, and backup features.
"""

import pulumi
import pulumi_aws as aws

# Get the current stack (dev, staging, prod)
stack = pulumi.get_stack()

# Common tags for all resources
common_tags = {
    "Project": "PurposePath",
    "ManagedBy": "Pulumi",
    "Environment": stack,
}

# DynamoDB Tables for Coaching Service
conversations_table = aws.dynamodb.Table(
    "coaching-conversations",
    name=f"purposepath-coaching-conversations-{stack}",
    billing_mode="PAY_PER_REQUEST",
    hash_key="conversation_id",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="conversation_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="user_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="tenant_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="created_at", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="tenant_id-user_id-index",
            hash_key="tenant_id",
            range_key="user_id",
            projection_type="ALL",
        ),
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="user_id-created_at-index",
            hash_key="user_id",
            range_key="created_at",
            projection_type="ALL",
        ),
    ],
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(enabled=True),
    tags={**common_tags, "Name": "coaching_conversations", "Purpose": "Conversation-Storage"},
)

coaching_sessions_table = aws.dynamodb.Table(
    "coaching-sessions",
    name=f"purposepath-coaching-sessions-{stack}",
    billing_mode="PAY_PER_REQUEST",
    hash_key="session_id",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="session_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="user_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="tenant_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="topic_id", type="S"),
    ],
    global_secondary_indexes=[
        # GSI for tenant + topic queries (one active session per tenant per topic)
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="tenant-topic-index",
            hash_key="tenant_id",
            range_key="topic_id",
            projection_type="ALL",
        ),
        # GSI for tenant + user queries (list sessions by user)
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="tenant-user-index",
            hash_key="tenant_id",
            range_key="user_id",
            projection_type="ALL",
        ),
    ],
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(enabled=True),
    tags={**common_tags, "Name": "coaching_sessions", "Purpose": "Session-Tracking"},
)

# S3 Bucket for LLM Prompts
prompts_bucket = aws.s3.Bucket(
    "coaching-prompts-bucket",
    bucket=f"purposepath-coaching-prompts-380276784420-{stack}",
    object_ownership="BucketOwnerEnforced",
    acl=None,
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ),
    tags={**common_tags, "Name": "coaching_prompts", "Purpose": "LLM-Prompt-Storage"},
)

# Block public access to prompts bucket
aws.s3.BucketPublicAccessBlock(
    "coaching-prompts-bucket-public-access-block",
    bucket=prompts_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ==========================================================================
# Secrets Manager - LLM Provider API Keys
# ==========================================================================
# These secrets store API keys for external LLM providers.
# Secret names are environment-agnostic (accessed by name, not ARN).
# Values should be updated manually or via Pulumi config for each environment.

# OpenAI API Key Secret
# NOTE: This secret was created externally and imported into Pulumi state.
# Secret values are managed manually via AWS Console or CLI, not via Pulumi.
openai_api_key_secret = aws.secretsmanager.Secret(
    "openai-api-key-secret",
    name=f"purposepath/{stack}/openai-api-key",
    description="OpenAI API key for PurposePath AI features",
    tags={**common_tags, "Name": "openai-api-key", "Purpose": "LLM-API-Key"},
    opts=pulumi.ResourceOptions(protect=True),
)

# Google Vertex AI Credentials Secret (Service Account JSON)
# NOTE: This secret was created externally and imported into Pulumi state.
# Secret values are managed manually via AWS Console or CLI, not via Pulumi.
google_vertex_credentials_secret = aws.secretsmanager.Secret(
    "google-vertex-credentials-secret",
    name=f"purposepath/{stack}/google-vertex-credentials",
    description="Google Vertex AI service account credentials",
    tags={**common_tags, "Name": "google-vertex-credentials", "Purpose": "LLM-API-Key"},
    opts=pulumi.ResourceOptions(protect=True),
)

# ==========================================================================
# Exports
# ==========================================================================
pulumi.export(
    "dynamoTables",
    {
        "coachingConversations": conversations_table.name,
        "coachingSessions": coaching_sessions_table.name,
    },
)
pulumi.export(
    "tableNames",
    {
        "conversations": f"purposepath-coaching-conversations-{stack}",
        "sessions": f"purposepath-coaching-sessions-{stack}",
    },
)
pulumi.export("promptsBucket", prompts_bucket.bucket)
pulumi.export(
    "secrets",
    {
        "openaiApiKey": openai_api_key_secret.name,
        "googleVertexCredentials": google_vertex_credentials_secret.name,
    },
)
pulumi.export(
    "tableArns",
    {
        "conversations": conversations_table.arn,
        "sessions": coaching_sessions_table.arn,
    },
)
