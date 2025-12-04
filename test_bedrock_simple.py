"""Simple test to verify Bedrock Anthropic access."""

import json
import sys

import boto3
from botocore.exceptions import ClientError


def test_bedrock_access():
    """Test if we can invoke Anthropic model."""
    print("Testing AWS Bedrock Anthropic Access...")
    print("=" * 60)

    try:
        # Create Bedrock runtime client
        print("1. Creating Bedrock runtime client...")
        runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
        print("   [PASS] Client created")

        # Prepare simple test message
        print("\n2. Preparing test message...")
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": "Say 'Hello from Bedrock!' and nothing else."}
            ],
        }
        print("   [PASS] Message prepared")

        # Invoke the model
        print("\n3. Invoking Anthropic Claude model...")
        print("   Model: anthropic.claude-3-sonnet-20240229-v1:0")
        print("   Region: us-east-1")

        response = runtime.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps(body),
            contentType="application/json",
        )

        print("   [PASS] Model invoked successfully!")

        # Parse response
        print("\n4. Parsing response...")
        response_body = json.loads(response["body"].read())
        content = response_body.get("content", [])

        if content and len(content) > 0:
            text = content[0].get("text", "")
            print(f"   [PASS] Response received: {text}")
        else:
            print("   [WARN] Response format unexpected")

        print("\n" + "=" * 60)
        print("SUCCESS! Bedrock Anthropic access is working!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Run: python test_website_scan.py")
        print("2. Deploy your application")
        print("3. Use the /api/v1/website/scan endpoint")

        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        print(f"\n   [FAIL] {error_code}")
        print("\n" + "=" * 60)

        if "ResourceNotFoundException" in error_code and "use case" in error_message.lower():
            print("FORM NOT APPROVED YET")
            print("=" * 60)
            print("\nThe use case form has not been processed yet.")
            print("\nPossible reasons:")
            print("1. Form submitted but still processing (wait 15-30 minutes)")
            print("2. Form not submitted successfully")
            print("3. Submitted for wrong region (must be us-east-1)")
            print("\nHow to verify:")
            print("1. Go to: https://console.aws.amazon.com/bedrock/")
            print("2. Select region: us-east-1 (top-right)")
            print("3. Click 'Model catalog'")
            print("4. Click any Anthropic Claude model")
            print("5. Click 'Open in Playground'")
            print("\nIf it opens playground without a form -> APPROVED")
            print("If it shows a form -> Fill it out again")

        elif "AccessDeniedException" in error_code:
            print("PERMISSION DENIED")
            print("=" * 60)
            print("\nYour IAM user/role lacks required permissions.")
            print("\nRequired permissions:")
            print("- bedrock:InvokeModel")
            print("- bedrock:InvokeModelWithResponseStream")
            print("\nContact your AWS administrator.")

        else:
            print(f"ERROR: {error_code}")
            print("=" * 60)
            print(f"\nError message: {error_message}")

        print("\nFull error details:")
        print(f"Code: {error_code}")
        print(f"Message: {error_message}")

        return False

    except Exception as e:
        print(f"\n   [FAIL] Unexpected error: {e}")
        print("\n" + "=" * 60)
        print("UNEXPECTED ERROR")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_bedrock_access()
    sys.exit(0 if success else 1)
