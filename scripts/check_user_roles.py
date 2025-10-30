"""Check user-tenant roles."""

import boto3

USER_ID = "6ca4f578-a7e6-4f58-84e5-26cc089515df"
TENANT_ID = "f937af6d-ea49-4bb4-bd65-38ef496da252"


def check_roles():
    """Check if user has roles assigned."""
    dynamodb = boto3.client("dynamodb")
    
    table_name = "purposepath-user-tenant-roles-dev"
    
    print(f"=== Checking roles for user ===")
    print(f"User ID: {USER_ID}")
    print(f"Tenant ID: {TENANT_ID}\n")
    
    try:
        # Scan for this user's roles
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": USER_ID}},
        )
        
        items = response.get("Items", [])
        
        if not items:
            print("⚠️  NO ROLES FOUND for this user!")
            print("\nThis is likely why API calls are forbidden.")
            print("\nNeed to add roles. Common roles:")
            print("  - Admin")
            print("  - User")
            print("  - TenantAdmin")
            return []
        
        print(f"Found {len(items)} role(s):\n")
        for item in items:
            role = {}
            for key, value in item.items():
                val = list(value.values())[0]
                role[key] = val
                print(f"  {key}: {val}")
            print()
        
        return items
        
    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    roles = check_roles()
    
    if not roles:
        print("\n💡 To add a role, we need to:")
        print("1. Create an entry in purposepath-user-tenant-roles-dev")
        print("2. Assign appropriate role (e.g., 'User' or 'Admin')")
