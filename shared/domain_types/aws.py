"""AWS service type definitions for PurposePath API.

DynamoDB types using inheritance pattern for unified operations.
Provides strong typing for AWS service operations.
"""

from decimal import Decimal
from typing import Any, NotRequired, TypedDict

# Type aliases matching boto3 DynamoDB AttributeValue structure
# DynamoDB AttributeValue can be: str, int, float, bool, bytes, bytearray, set, list, dict, Decimal, None
DynamoDBAttributeValue = (
    str
    | int
    | float
    | bool
    | bytes
    | bytearray
    | Decimal
    | None
    | list[Any]
    | dict[str, Any]
    | set[str]
    | set[int]
    | set[bytes]
)

# JSONValue is for general JSON serialization (subset of DynamoDBAttributeValue)
JSONValue = str | int | float | bool | None | dict[str, Any] | list[Any] | Decimal


class QueryOutputTypeDef(TypedDict, total=False):
    """DynamoDB Query operation output"""

    Items: NotRequired[list[dict[str, JSONValue]]]
    Count: NotRequired[int]
    ScannedCount: NotRequired[int]
    LastEvaluatedKey: NotRequired[dict[str, JSONValue]]
    ConsumedCapacity: NotRequired[dict[str, JSONValue]]


class ScanOutputTypeDef(TypedDict, total=False):
    """DynamoDB Scan operation output"""

    Items: NotRequired[list[dict[str, JSONValue]]]
    Count: NotRequired[int]
    ScannedCount: NotRequired[int]
    LastEvaluatedKey: NotRequired[dict[str, JSONValue]]
    ConsumedCapacity: NotRequired[dict[str, JSONValue]]


class PutItemOutputTypeDef(TypedDict, total=False):
    """DynamoDB PutItem operation output"""

    Attributes: NotRequired[dict[str, JSONValue]]
    ConsumedCapacity: NotRequired[dict[str, JSONValue]]
    ItemCollectionMetrics: NotRequired[dict[str, JSONValue]]


class UpdateItemOutputTypeDef(TypedDict, total=False):
    """DynamoDB UpdateItem operation output"""

    Attributes: NotRequired[dict[str, JSONValue]]
    ConsumedCapacity: NotRequired[dict[str, JSONValue]]
    ItemCollectionMetrics: NotRequired[dict[str, JSONValue]]


class DeleteItemOutputTypeDef(TypedDict, total=False):
    """DynamoDB DeleteItem operation output"""

    Attributes: NotRequired[dict[str, JSONValue]]
    ConsumedCapacity: NotRequired[dict[str, JSONValue]]
    ItemCollectionMetrics: NotRequired[dict[str, JSONValue]]


class GetItemOutputTypeDef(TypedDict, total=False):
    """DynamoDB GetItem operation output"""

    Item: NotRequired[dict[str, JSONValue]]
    ConsumedCapacity: NotRequired[dict[str, JSONValue]]


class DynamoDBKey(TypedDict, total=False):
    """Primary key structure for DynamoDB items"""

    pk: str  # Partition key
    sk: NotRequired[str]  # Sort key (optional)


class DynamoDBItem(TypedDict, total=False):
    """Base DynamoDB item structure"""

    pk: str
    sk: NotRequired[str]
    tenant_id: NotRequired[str]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]
    ttl: NotRequired[int]


# Lambda types
class LambdaContext:
    """AWS Lambda context object"""

    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    remaining_time_in_millis: int
    request_id: str
    log_group_name: str
    log_stream_name: str
    identity: Any
    client_context: Any

    def get_remaining_time_in_millis(self) -> int:
        """Get remaining execution time in milliseconds"""
        return self.remaining_time_in_millis


# API Gateway types
class APIGatewayProxyEvent(TypedDict, total=False):
    """API Gateway Lambda proxy integration event"""

    resource: str
    path: str
    httpMethod: str
    headers: NotRequired[dict[str, str]]
    multiValueHeaders: NotRequired[dict[str, list[str]]]
    queryStringParameters: NotRequired[dict[str, str]]
    multiValueQueryStringParameters: NotRequired[dict[str, list[str]]]
    pathParameters: NotRequired[dict[str, str]]
    stageVariables: NotRequired[dict[str, str]]
    requestContext: dict[str, Any]
    body: NotRequired[str]
    isBase64Encoded: bool


class APIGatewayProxyResponse(TypedDict, total=False):
    """API Gateway Lambda proxy integration response"""

    statusCode: int
    headers: NotRequired[dict[str, str]]
    multiValueHeaders: NotRequired[dict[str, list[str]]]
    body: NotRequired[str]
    isBase64Encoded: NotRequired[bool]
