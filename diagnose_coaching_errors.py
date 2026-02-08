"""Diagnostic script to investigate coaching session 500 errors.

This script checks:
1. S3 template existence for active coaching topics
2. DynamoDB topic configuration
3. Common configuration issues
"""

import asyncio

import boto3

from coaching.src.core.config_multitenant import settings
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage


async def check_templates_exist(topic_id: str, s3_storage: S3PromptStorage) -> dict:
    """Check if all required templates exist for a topic."""
    results = {}
    required_templates = ["system", "initiation", "resume"]

    for template_type in required_templates:
        try:
            exists = await s3_storage.prompt_exists(topic_id=topic_id, prompt_type=template_type)
            results[template_type] = {"exists": exists, "error": None}
            if exists:
                # Try to load it
                content = await s3_storage.get_prompt(topic_id=topic_id, prompt_type=template_type)
                results[template_type]["loaded"] = content is not None
                results[template_type]["size"] = len(content) if content else 0
        except Exception as e:
            results[template_type] = {"exists": False, "error": str(e)}

    return results


async def diagnose():
    """Run diagnostic checks."""
    print("=" * 80)
    print("COACHING SESSION 500 ERROR DIAGNOSTICS")
    print("=" * 80)
    print()

    # Initialize services
    print("1. Checking Configuration...")
    print(f"   AWS Region: {settings.aws_region}")
    print(f"   Bedrock Region: {settings.bedrock_region}")
    print(f"   Topics Table: {settings.topics_table}")
    print(f"   Sessions Table: {settings.coaching_sessions_table}")
    print(f"   Prompts Bucket: {settings.prompts_bucket}")
    print()

    try:
        # Initialize DynamoDB
        dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
        topic_repo = TopicRepository(
            dynamodb_resource=dynamodb_resource,
            table_name=settings.topics_table,
        )

        # Initialize S3
        s3_client = boto3.client("s3", region_name=settings.aws_region)
        s3_storage = S3PromptStorage(
            bucket_name=settings.prompts_bucket,
            s3_client=s3_client,
        )

        print("2. Checking Active Coaching Topics...")
        print()

        # Get active topics with topic_type = 'conversation'
        # Note: Using list_all as GSI may not be available
        try:
            conversation_topics = await topic_repo.list_by_type(
                topic_type="conversation", include_inactive=False
            )
        except Exception as gsi_error:
            print(f"   [WARNING] Cannot query by type - GSI missing: {gsi_error}")
            print("   [INFO] Falling back to scan all topics...")
            all_topics = await topic_repo.list_all(include_inactive=False)
            conversation_topics = [t for t in all_topics if t.topic_type == "conversation"]

        print(f"   Found {len(conversation_topics)} active conversation topics")
        print()

        if not conversation_topics:
            print("   WARNING: No active conversation topics found!")
            print("   This could mean topics are not properly configured in DynamoDB.")
            print()

            # Show what topics do exist
            all_topics_list = await topic_repo.list_all(include_inactive=False)
            if all_topics_list:
                print("   Available active topics (by type):")
                topic_types = {}
                for t in all_topics_list:
                    if t.topic_type not in topic_types:
                        topic_types[t.topic_type] = []
                    topic_types[t.topic_type].append(t)

                for topic_type, topics in sorted(topic_types.items()):
                    print(f"     - {topic_type}: {len(topics)} topics")
                    for t in topics[:3]:  # Show first 3
                        print(f"         * {t.topic_id} - {t.topic_name}")
                print()

        # Check templates for each topic
        issues_found = []

        for topic in conversation_topics:
            print(f"3. Checking Templates for: {topic.topic_name} ({topic.topic_id})")
            print(f"   Category: {topic.category}")
            print(f"   Description: {topic.description}")

            template_results = await check_templates_exist(topic.topic_id, s3_storage)

            for template_type, result in template_results.items():
                status = "[OK]" if result["exists"] and result.get("loaded", False) else "[FAIL]"
                if result["error"]:
                    print(f"   {status} {template_type:12s} ERROR: {result['error']}")
                    issues_found.append(f"{topic.topic_id}/{template_type}: {result['error']}")
                elif not result["exists"]:
                    print(f"   {status} {template_type:12s} MISSING")
                    issues_found.append(
                        f"{topic.topic_id}/{template_type}: Template not found in S3"
                    )
                else:
                    size = result.get("size", 0)
                    print(f"   {status} {template_type:12s} OK ({size} bytes)")

            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)

        if issues_found:
            print(f"\n[ERROR] Found {len(issues_found)} issue(s):\n")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")
            print()
            print("RECOMMENDATION:")
            print("   - Upload missing templates to S3 bucket:", settings.prompts_bucket)
            print("   - Path format: prompts/{topic_id}/{template_type}.md")
            print("   - Required templates: system.md, initiation.md, resume.md")
        else:
            print("\n[SUCCESS] All templates are present and loadable!")
            print()
            print("OTHER POSSIBLE CAUSES OF 500 ERRORS:")
            print("   1. JWT token issues - check Authorization header")
            print("   2. Parameter enrichment failures - check Business API connectivity")
            print("   3. LLM provider errors - check Bedrock access and quotas")
            print("   4. DynamoDB access issues - check session table permissions")

        print()

    except Exception as e:
        print(f"\n[FATAL] ERROR: {e}")
        print(f"   Error Type: {type(e).__name__}")
        import traceback

        print()
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose())
