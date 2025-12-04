"""Activate user account by updating status in DynamoDB."""

import sys

import boto3
from botocore.exceptions import ClientError

USER_ID = "6ca4f578-a7e6-4f58-84e5-26cc089515df"


def find_users_table():
    """Find the DynamoDB users table."""
    dynamodb = boto3.client("dynamodb")

    try:
        tables = dynamodb.list_tables()["TableNames"]
        print(f"Found {len(tables)} tables")

        # Look for users table - prefer purposepath-users-dev
        user_tables = [t for t in tables if "user" in t.lower() and "dev" in t.lower()]
        print(f"User tables: {user_tables}")

        # Prefer exact match
        if "purposepath-users-dev" in user_tables:
            return "purposepath-users-dev"

        if user_tables:
            return user_tables[0]

        return None
    except Exception as e:
        print(f"Error listing tables: {e}")
        return None


def update_user_status(table_name, user_id, new_status="Active"):
    """Update user status in DynamoDB."""
    dynamodb = boto3.client("dynamodb")

    try:
        print(f"\nUpdating user {user_id} in table {table_name}")
        print(f"Setting status to: {new_status}")

        response = dynamodb.update_item(
            TableName=table_name,
            Key={"id": {"S": user_id}},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": {"S": new_status}},
            ReturnValues="ALL_NEW",
        )

        print("\n✅ User status updated successfully!")
        print(f"New attributes: {response.get('Attributes', {})}")
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            print(f"\n❌ Table '{table_name}' not found")
            # Try common variations
            alternatives = [
                "purposepath-users-dev",
                "users-dev",
                "account-users-dev",
                "PurposePath-Users-Dev",
            ]
            print(f"Try one of these: {alternatives}")
        else:
            print(f"\n❌ Error updating user: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=== User Account Activation ===")
    print(f"User ID: {USER_ID}")
    print()

    # Find table
    table_name = find_users_table()

    if not table_name:
        print("\n⚠️  Could not auto-detect users table.")
        print("Please specify table name manually:")
        table_name = input("Table name: ").strip()
        if not table_name:
            print("No table name provided. Exiting.")
            sys.exit(1)

    # Update status
    success = update_user_status(table_name, USER_ID, "Active")

    if success:
        print("\n🎉 User activated! You can now run E2E tests.")
        print("Run: .venv\\Scripts\\python.exe -m pytest coaching/tests/e2e/ -v -m e2e")
    else:
        sys.exit(1)
