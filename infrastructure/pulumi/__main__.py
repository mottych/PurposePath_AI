"""PurposePath Infrastructure - DynamoDB Tables.

This Pulumi project manages the core DynamoDB tables for the PurposePath AI platform.
Tables are configured with on-demand billing, appropriate indexes, and backup features.
"""

import pulumi
import pulumi_aws as aws

# Common tags for all resources
common_tags = {
    "Project": "PurposePath",
    "ManagedBy": "Pulumi",
    "Environment": pulumi.get_stack(),
}

# DynamoDB Tables for Coaching Service
conversations_table = aws.dynamodb.Table(
    "coaching-conversations",
    name="purposepath-coaching-conversations-dev",
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
    name="purposepath-coaching-sessions-dev",
    billing_mode="PAY_PER_REQUEST",
    hash_key="session_id",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="session_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="user_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="tenant_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="topic", type="S"),
        aws.dynamodb.TableAttributeArgs(name="started_at", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="tenant_id-user_id-index",
            hash_key="tenant_id",
            range_key="user_id",
            projection_type="ALL",
        ),
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="user_id-topic-index",
            hash_key="user_id",
            range_key="topic",
            projection_type="ALL",
        ),
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="tenant_id-started_at-index",
            hash_key="tenant_id",
            range_key="started_at",
            projection_type="ALL",
        ),
    ],
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(enabled=True),
    tags={**common_tags, "Name": "coaching_sessions", "Purpose": "Session-Tracking"},
)

llm_prompts_table = aws.dynamodb.Table(
    "llm-prompts",
    name="purposepath-llm-prompts-dev",
    billing_mode="PAY_PER_REQUEST",
    hash_key="topic_id",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="topic_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="topic_type", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="topic_type-index",
            hash_key="topic_type",
            projection_type="ALL",
        ),
    ],
    stream_enabled=True,
    stream_view_type="NEW_AND_OLD_IMAGES",
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(enabled=True),
    tags={**common_tags, "Name": "llm_prompts", "Purpose": "LLM-Prompt-Management"},
)

# S3 Bucket for LLM Prompts
prompts_bucket = aws.s3.Bucket(
    "coaching-prompts-bucket",
    bucket="purposepath-coaching-prompts-380276784420-dev",
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

# Exports
pulumi.export("dynamoTables", {
    "coachingConversations": conversations_table.name,
    "coachingSessions": coaching_sessions_table.name,
    "llmPrompts": llm_prompts_table.name,
})
pulumi.export("tableNames", {
    "conversations": "purposepath-coaching-conversations-dev",
    "sessions": "purposepath-coaching-sessions-dev",
    "prompts": "purposepath-llm-prompts-dev",
})
pulumi.export("promptsBucket", prompts_bucket.bucket)
pulumi.export("tableArns", {
    "conversations": conversations_table.arn,
    "sessions": coaching_sessions_table.arn,
    "prompts": llm_prompts_table.arn,
})
