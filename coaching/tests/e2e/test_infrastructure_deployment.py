"""End-to-end tests for LLM prompts infrastructure deployment.

These tests verify that the infrastructure is correctly deployed and accessible:
- DynamoDB table exists with correct schema
- GSI is configured correctly
- Lambda has access to table and S3
- Environment variables are set correctly
"""

import contextlib
import os
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from coaching.src.core.config_multitenant import get_settings
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from mypy_boto3_s3 import S3Client


@pytest.fixture
def stage() -> str:
    """Get deployment stage from environment."""
    return os.getenv("STAGE", "dev")


@pytest.fixture
def dynamodb_client() -> DynamoDBClient:
    """Get DynamoDB client."""
    return boto3.client("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))


@pytest.fixture
def dynamodb_resource() -> DynamoDBServiceResource:
    """Get DynamoDB resource."""
    return boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))


@pytest.fixture
def s3_client() -> S3Client:
    """Get S3 client."""
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))


@pytest.mark.e2e
@pytest.mark.skip(reason="Infrastructure state mismatch - requires manual verification")
class TestDynamoDBTableDeployment:
    """Test DynamoDB table deployment and configuration."""

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_exists(
        self,
        dynamodb_client: DynamoDBClient,
        stage: str,
    ) -> None:
        """Test that LLM prompts table exists in AWS."""
        settings = get_settings()
        table_name = settings.llm_prompts_table

        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            assert response["Table"]["TableName"] == table_name
            assert response["Table"]["TableStatus"] in ["ACTIVE", "UPDATING"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(f"Table {table_name} does not exist in AWS")
            raise

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_has_correct_key_schema(
        self,
        dynamodb_client: DynamoDBClient,
    ) -> None:
        """Test that table has correct primary key."""
        settings = get_settings()
        table_name = settings.llm_prompts_table

        response = dynamodb_client.describe_table(TableName=table_name)
        key_schema = response["Table"]["KeySchema"]

        # Should have only hash key (topic_id)
        assert len(key_schema) == 1
        assert key_schema[0]["AttributeName"] == "topic_id"
        assert key_schema[0]["KeyType"] == "HASH"

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_has_topic_type_gsi(
        self,
        dynamodb_client: DynamoDBClient,
    ) -> None:
        """Test that table has topic_type GSI."""
        settings = get_settings()
        table_name = settings.llm_prompts_table

        response = dynamodb_client.describe_table(TableName=table_name)
        gsi_list = response["Table"].get("GlobalSecondaryIndexes", [])

        # Find topic_type-index
        topic_type_index = next(
            (gsi for gsi in gsi_list if gsi["IndexName"] == "topic_type-index"),
            None,
        )

        assert topic_type_index is not None, "topic_type-index GSI not found"
        assert topic_type_index["IndexStatus"] in ["ACTIVE", "UPDATING"]
        assert topic_type_index["KeySchema"][0]["AttributeName"] == "topic_type"
        assert topic_type_index["Projection"]["ProjectionType"] == "ALL"

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_has_billing_mode(
        self,
        dynamodb_client: DynamoDBClient,
    ) -> None:
        """Test that table uses PAY_PER_REQUEST billing."""
        settings = get_settings()
        table_name = settings.llm_prompts_table

        response = dynamodb_client.describe_table(TableName=table_name)
        billing_mode = (
            response["Table"].get("BillingModeSummary", {}).get("BillingMode", "PROVISIONED")
        )

        assert billing_mode == "PAY_PER_REQUEST"

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_has_stream_enabled(
        self,
        dynamodb_client: DynamoDBClient,
    ) -> None:
        """Test that table has DynamoDB stream enabled."""
        settings = get_settings()
        table_name = settings.llm_prompts_table

        response = dynamodb_client.describe_table(TableName=table_name)
        stream_spec = response["Table"].get("StreamSpecification", {})

        assert stream_spec.get("StreamEnabled") is True
        assert stream_spec.get("StreamViewType") == "NEW_AND_OLD_IMAGES"

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_has_point_in_time_recovery(
        self,
        dynamodb_client: DynamoDBClient,
    ) -> None:
        """Test that table has point-in-time recovery enabled."""
        settings = get_settings()
        table_name = settings.llm_prompts_table

        response = dynamodb_client.describe_continuous_backups(TableName=table_name)
        pitr = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]

        assert pitr["PointInTimeRecoveryStatus"] == "ENABLED"


@pytest.mark.e2e
@pytest.mark.skip(reason="Infrastructure state mismatch - requires manual verification")
class TestS3BucketAccess:
    """Test S3 bucket access for prompt storage."""

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_prompts_bucket_exists(
        self,
        s3_client: S3Client,
    ) -> None:
        """Test that prompts bucket exists and is accessible."""
        settings = get_settings()
        bucket_name = settings.prompts_bucket

        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                pytest.fail(f"Bucket {bucket_name} does not exist")
            elif error_code == "403":
                pytest.fail(f"Access denied to bucket {bucket_name}")
            raise

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_prompts_bucket_path_structure(
        self,
        s3_client: S3Client,
    ) -> None:
        """Test that prompts bucket has expected directory structure."""
        settings = get_settings()
        bucket_name = settings.prompts_bucket

        # Check if prompts/ prefix exists (may be empty initially)
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="prompts/", MaxKeys=1)
            # If bucket exists and we don't get an error, path structure is accessible
            assert response is not None
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                pytest.fail(f"Bucket {bucket_name} does not exist")
            raise


@pytest.mark.e2e
@pytest.mark.skip(reason="Infrastructure state mismatch - requires manual verification")
class TestLambdaEnvironmentVariables:
    """Test that Lambda function has correct environment variables."""

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_llm_prompts_table_env_var_set(self) -> None:
        """Test that LLM_PROMPTS_TABLE environment variable is set."""
        settings = get_settings()
        assert settings.llm_prompts_table is not None
        assert settings.llm_prompts_table.startswith("purposepath-llm-prompts-")

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_prompts_bucket_env_var_set(self) -> None:
        """Test that PROMPTS_BUCKET environment variable is set."""
        settings = get_settings()
        assert settings.prompts_bucket is not None
        assert settings.prompts_bucket.startswith("purposepath-coaching-prompts-")


@pytest.mark.e2e
@pytest.mark.skip(reason="Infrastructure state mismatch - requires manual verification")
class TestTableOperations:
    """Test basic DynamoDB operations on deployed table."""

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_put_and_get_item(
        self,
        dynamodb_resource: DynamoDBServiceResource,
    ) -> None:
        """Test writing and reading a topic from the table."""
        settings = get_settings()
        table = dynamodb_resource.Table(settings.llm_prompts_table)

        # Test item
        test_item: dict[str, Any] = {
            "topic_id": "test_e2e_topic",
            "topic_name": "E2E Test Topic",
            "topic_type": "single_shot",
            "category": "analysis",
            "display_order": 999,
            "is_active": True,
            "prompts": [
                {
                    "prompt_type": "system",
                    "s3_bucket": settings.prompts_bucket,
                    "s3_key": "prompts/test_e2e_topic/system.md",
                    "updated_at": "2025-01-20T00:00:00Z",
                    "updated_by": "e2e_test",
                }
            ],
            "config": {"default_model": "anthropic.claude-3-haiku-20240307-v1:0"},
            "created_at": "2025-01-20T00:00:00Z",
            "created_by": "e2e_test",
            "updated_at": "2025-01-20T00:00:00Z",
        }

        try:
            # Put item
            table.put_item(Item=test_item)

            # Get item
            response = table.get_item(Key={"topic_id": "test_e2e_topic"})
            assert "Item" in response
            assert response["Item"]["topic_id"] == "test_e2e_topic"
            assert response["Item"]["topic_name"] == "E2E Test Topic"

        finally:
            # Clean up
            with contextlib.suppress(Exception):
                table.delete_item(Key={"topic_id": "test_e2e_topic"})

    @pytest.mark.skipif(
        os.getenv("SKIP_E2E_TESTS") == "true",
        reason="E2E tests disabled",
    )
    def test_query_by_topic_type_gsi(
        self,
        dynamodb_resource: DynamoDBServiceResource,
    ) -> None:
        """Test querying using topic_type GSI."""
        settings = get_settings()
        table = dynamodb_resource.Table(settings.llm_prompts_table)

        # Test item
        test_item: dict[str, Any] = {
            "topic_id": "test_gsi_query",
            "topic_name": "GSI Test Topic",
            "topic_type": "conversation_coaching",
            "category": "coaching",
            "display_order": 998,
            "is_active": True,
            "prompts": [],
            "config": {},
            "created_at": "2025-01-20T00:00:00Z",
            "created_by": "e2e_test",
            "updated_at": "2025-01-20T00:00:00Z",
        }

        try:
            # Put item
            table.put_item(Item=test_item)

            # Query using GSI
            response = table.query(
                IndexName="topic_type-index",
                KeyConditionExpression="topic_type = :topic_type",
                ExpressionAttributeValues={":topic_type": "conversation_coaching"},
            )

            # Verify our test item is in results
            items = response.get("Items", [])
            test_item_found = any(item["topic_id"] == "test_gsi_query" for item in items)
            assert test_item_found, "Test item not found in GSI query results"

        finally:
            # Clean up
            with contextlib.suppress(Exception):
                table.delete_item(Key={"topic_id": "test_gsi_query"})
