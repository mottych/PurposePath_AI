"""Check Lambda function status and last modified time."""

import boto3


def check_lambda():
    lambda_client = boto3.client("lambda", region_name="us-east-1")

    # List all functions and filter for coaching
    response = lambda_client.list_functions()

    coaching_functions = [
        f for f in response["Functions"] if "coaching" in f["FunctionName"].lower()
    ]

    if not coaching_functions:
        print("No coaching Lambda functions found!")
        return

    for func in coaching_functions:
        print(f"\n=== {func['FunctionName']} ===")
        print(f"Last Modified: {func['LastModified']}")
        print(f"Code Size: {func['CodeSize']:,} bytes")
        print(f"Package Type: {func.get('PackageType', 'Zip')}")

        if func.get("PackageType") == "Image":
            print(f"Image Code SHA: {func.get('CodeSha256', 'N/A')}")
        else:
            print(f"Runtime: {func.get('Runtime', 'N/A')}")


if __name__ == "__main__":
    check_lambda()
