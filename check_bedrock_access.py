"""Check AWS Bedrock access and permissions."""

import sys

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def check_credentials():
    """Check if AWS credentials are configured."""
    print("=" * 60)
    print("1. Checking AWS Credentials")
    print("=" * 60)
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print("✅ AWS Credentials configured")
        print(f"   Account: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Run: aws configure")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_iam_permissions():
    """Check IAM permissions for Bedrock."""
    print("\n" + "=" * 60)
    print("2. Checking IAM Permissions")
    print("=" * 60)

    try:
        iam = boto3.client("iam")
        sts = boto3.client("sts")

        # Get current user
        identity = sts.get_caller_identity()
        arn = identity["Arn"]

        print(f"Checking permissions for: {arn}")

        # Try to simulate Bedrock permissions
        # Note: This requires iam:SimulatePrincipalPolicy permission
        try:
            response = iam.simulate_principal_policy(
                PolicySourceArn=arn,
                ActionNames=[
                    "bedrock:InvokeModel",
                    "bedrock:ListFoundationModels",
                    "bedrock:PutUseCaseForModelAccess",
                    "aws-marketplace:Subscribe",
                ],
            )

            for result in response["EvaluationResults"]:
                action = result["EvalActionName"]
                decision = result["EvalDecision"]
                if decision == "allowed":
                    print(f"   ✅ {action}")
                else:
                    print(f"   ❌ {action} - {decision}")

            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                print("   ⚠️  Cannot check permissions (need iam:SimulatePrincipalPolicy)")
                print("   Attempting direct Bedrock test instead...")
                return True
            raise

    except Exception as e:
        print(f"   ⚠️  Could not check IAM permissions: {e}")
        print("   Will attempt Bedrock API calls directly...")
        return True


def check_bedrock_access():
    """Check Bedrock API access."""
    print("\n" + "=" * 60)
    print("3. Checking Bedrock API Access")
    print("=" * 60)

    try:
        bedrock = boto3.client("bedrock", region_name="us-east-1")

        # Try to list foundation models
        print("Attempting to list foundation models...")
        response = bedrock.list_foundation_models()

        models = response.get("modelSummaries", [])
        print(f"✅ Can access Bedrock API ({len(models)} models available)")

        # Count Anthropic models
        anthropic_models = [m for m in models if "anthropic" in m["modelId"].lower()]
        print(f"   Found {len(anthropic_models)} Anthropic models")

        if anthropic_models:
            print("\n   Available Anthropic models:")
            for model in anthropic_models[:5]:  # Show first 5
                print(f"   - {model['modelId']}")
                print(f"     Status: {model.get('modelLifecycle', {}).get('status', 'ACTIVE')}")

        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        print(f"❌ Bedrock API Error: {error_code}")
        print(f"   {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_anthropic_model():
    """Test actual Anthropic model invocation."""
    print("\n" + "=" * 60)
    print("4. Testing Anthropic Model Invocation")
    print("=" * 60)

    try:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        print(f"Testing model: {model_id}")

        # Simple test prompt
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say 'Hello, Bedrock!' and nothing else."}],
        }

        print("Invoking model with test prompt...")

        import json

        response = bedrock_runtime.invoke_model(
            modelId=model_id, body=json.dumps(body), contentType="application/json"
        )

        response_body = json.loads(response["body"].read())
        content = response_body.get("content", [])

        if content:
            text = content[0].get("text", "")
            print("✅ Model invocation successful!")
            print(f"   Response: {text}")
            return True
        else:
            print("⚠️  Model responded but with unexpected format")
            return False

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        if error_code == "ResourceNotFoundException":
            if "use case details" in error_message.lower():
                print("❌ Use case form not submitted")
                print("\n📋 ACTION REQUIRED:")
                print("   1. Open AWS Bedrock Console: https://console.aws.amazon.com/bedrock/")
                print("   2. Go to Model Catalog")
                print("   3. Click on any Anthropic Claude model")
                print("   4. Click 'Open in Playground'")
                print("   5. Fill out the use case form when prompted")
                print("   6. Submit and wait for approval (usually immediate)")
                print(f"\n   Full error: {error_message}")
            else:
                print(f"❌ Model not found: {error_code}")
                print(f"   {error_message}")
        elif error_code == "AccessDeniedException":
            print(f"❌ Access denied: {error_code}")
            print(f"   {error_message}")
            print("\n📋 ACTION REQUIRED:")
            print("   Your IAM user/role needs these permissions:")
            print("   - bedrock:InvokeModel")
            print("   - bedrock:InvokeModelWithResponseStream")
        else:
            print(f"❌ Error: {error_code}")
            print(f"   {error_message}")

        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("AWS Bedrock Access Verification")
    print("=" * 60)

    # Run checks
    creds_ok = check_credentials()
    if not creds_ok:
        print("\n❌ Cannot proceed without AWS credentials")
        sys.exit(1)

    perms_ok = check_iam_permissions()
    bedrock_ok = check_bedrock_access()

    if not bedrock_ok:
        print("\n❌ Cannot access Bedrock API")
        sys.exit(1)

    model_ok = test_anthropic_model()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"AWS Credentials:      {'✅ PASS' if creds_ok else '❌ FAIL'}")
    print(f"IAM Permissions:      {'✅ PASS' if perms_ok else '⚠️  CHECK'}")
    print(f"Bedrock API Access:   {'✅ PASS' if bedrock_ok else '❌ FAIL'}")
    print(f"Anthropic Model Test: {'✅ PASS' if model_ok else '❌ FAIL'}")
    print("=" * 60)

    if model_ok:
        print("\n🎉 SUCCESS! Bedrock is fully configured and working!")
        print("\nNext steps:")
        print("1. Run: python test_website_scan.py")
        print("2. Deploy your application")
        print("3. Test the /api/v1/website/scan endpoint")
    elif not model_ok and bedrock_ok:
        print("\n⚠️  Bedrock API works, but Anthropic model needs use case submission")
        print("\nSee BEDROCK_ACCESS_SETUP.md for detailed instructions")
    else:
        print("\n❌ Bedrock access not fully configured")
        print("\nSee BEDROCK_ACCESS_SETUP.md for troubleshooting steps")

    return 0 if model_ok else 1


if __name__ == "__main__":
    sys.exit(main())
