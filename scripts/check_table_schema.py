"""Check DynamoDB table schema."""

import boto3


def check_table_schema(table_name):
    """Check table schema and sample data."""
    dynamodb = boto3.client("dynamodb")

    try:
        # Get table description
        response = dynamodb.describe_table(TableName=table_name)
        table = response["Table"]

        print(f"=== Table: {table_name} ===\n")
        print("Key Schema:")
        for key in table["KeySchema"]:
            print(f"  - {key['AttributeName']} ({key['KeyType']})")

        print("\nAttribute Definitions:")
        for attr in table["AttributeDefinitions"]:
            print(f"  - {attr['AttributeName']}: {attr['AttributeType']}")

        # Try to scan for sample items
        print("\nSample Items:")
        scan_response = dynamodb.scan(TableName=table_name, Limit=2)
        for i, item in enumerate(scan_response.get("Items", []), 1):
            print(f"\n  Item {i}:")
            for key, value in item.items():
                # Get the actual value
                val = next(iter(value.values())) if value else None
                if isinstance(val, str) and len(val) > 50:
                    val = val[:50] + "..."
                print(f"    {key}: {val}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys

    table = sys.argv[1] if len(sys.argv) > 1 else "purposepath-users-dev"
    check_table_schema(table)
