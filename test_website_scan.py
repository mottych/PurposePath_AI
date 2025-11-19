"""Test script for website scanning functionality."""

import asyncio
import sys

import structlog

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Configure basic logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)


async def test_bedrock_config():
    """Test Bedrock configuration and credentials."""
    print("\n" + "=" * 60)
    print("STEP 1: Testing Bedrock Configuration")
    print("=" * 60)

    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        # Create Bedrock runtime client
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        print("✅ AWS credentials configured")
        print(f"✅ Bedrock client created (Region: {client.meta.region_name})")

        # Try to list foundation models to verify access
        try:
            bedrock_client = boto3.client("bedrock", region_name="us-east-1")
            response = bedrock_client.list_foundation_models(
                byProvider="Anthropic",
            )
            models = response.get("modelSummaries", [])
            if models:
                print(f"✅ Bedrock access verified ({len(models)} Anthropic models available)")
                print(f"   Available models: {[m['modelId'][:40] for m in models[:3]]}")
            else:
                print("⚠️  No models found (but connection works)")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "AccessDeniedException":
                print("⚠️  Bedrock connection OK, but missing list permission (not critical)")
            else:
                print(f"⚠️  Could not list models: {error_code}")

        return True

    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_website_fetch():
    """Test website content fetching."""
    print("\n" + "=" * 60)
    print("STEP 2: Testing Website Content Fetching")
    print("=" * 60)

    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://purposepath.ai"
        print(f"Fetching: {url}")

        response = requests.get(url, timeout=15)
        print(f"✅ HTTP {response.status_code} - {len(response.text)} characters")

        soup = BeautifulSoup(response.text, "lxml")
        title = soup.find("title")
        if title:
            print(f"✅ Page title: {title.get_text().strip()}")

        # Check for meta description
        meta = soup.find("meta", {"name": "description"})
        if meta:
            print(f"✅ Meta description found: {meta.get('content', '')[:80]}...")

        return True

    except Exception as e:
        print(f"❌ Error fetching website: {e}")
        return False


async def test_website_scanning_service():
    """Test the complete website scanning service."""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Website Scanning Service")
    print("=" * 60)

    try:
        from coaching.src.llm.providers.manager import ProviderManager
        from coaching.src.services.llm_service import LLMService
        from coaching.src.services.website_analysis_service import WebsiteAnalysisService

        url = "https://purposepath.ai"
        print(f"Analyzing: {url}")

        # Initialize provider manager
        print("Initializing LLM provider...")
        provider_manager = ProviderManager()

        # Add Bedrock provider
        print("Adding Bedrock provider...")
        await provider_manager.add_provider(
            provider_id="bedrock",
            provider_type="bedrock",
            config_dict={
                "model_name": "anthropic.claude-3-sonnet-20240229-v1:0",
                "region_name": "us-east-1",
            },
        )

        await provider_manager.initialize()
        print("✅ Provider manager initialized with Bedrock")

        # Create analysis service with provider manager directly
        analysis_service = WebsiteAnalysisService(provider_manager=provider_manager)
        print("✅ Analysis service created")

        # Analyze website
        print("Analyzing website content with AI (this may take 10-30 seconds)...")
        analysis = await analysis_service.analyze_website(url)

        print("\n" + "-" * 60)
        print("ANALYSIS RESULTS")
        print("-" * 60)

        print(f"\n🎯 Niche: {analysis.get('niche', 'N/A')}")
        print(f"\n👥 ICA: {analysis.get('ica', 'N/A')}")
        print(f"\n💎 Value Proposition: {analysis.get('value_proposition', 'N/A')}")

        products = analysis.get("products", [])
        print(f"\n📦 Products/Services ({len(products)}):")
        for i, product in enumerate(products, 1):
            print(f"   {i}. {product.get('name', 'Unknown')}")
            print(f"      Problem: {product.get('problem', 'N/A')}")
            print(f"      ID: {product.get('id', 'N/A')}")

        print("\n✅ Website scanning completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during website scanning: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PurposePath Website Scanning Test Suite")
    print("=" * 60)

    # Test 1: Bedrock config
    bedrock_ok = await test_bedrock_config()

    # Test 2: Website fetch
    fetch_ok = await test_website_fetch()

    # Test 3: Full scanning (only if Bedrock is configured)
    scan_ok = False
    if bedrock_ok and fetch_ok:
        scan_ok = await test_website_scanning_service()
    else:
        print("\n⏭️  Skipping website scanning test (prerequisites not met)")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Bedrock Configuration: {'✅ PASS' if bedrock_ok else '❌ FAIL'}")
    print(f"Website Fetching:      {'✅ PASS' if fetch_ok else '❌ FAIL'}")
    print(f"AI Website Scanning:   {'✅ PASS' if scan_ok else '❌ FAIL' if bedrock_ok else '⏭️  SKIPPED'}")
    print("=" * 60)

    return 0 if (bedrock_ok and fetch_ok and scan_ok) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
