"""External API type definitions for PurposePath API.

Types for third-party service integrations.
Provides strong typing for external API interactions.
"""

from typing import Literal, NotRequired, TypedDict

from .common import ISODateString, JSONValue

# ========================================
# Google Authentication Types
# ========================================

class GoogleUserInfo(TypedDict):
    """Google OAuth user information"""
    id: str
    email: str
    verified_email: bool
    name: str
    given_name: str
    family_name: str
    picture: str
    locale: NotRequired[str]

class GoogleTokenInfo(TypedDict):
    """Google OAuth token information"""
    access_token: str
    refresh_token: NotRequired[str]
    id_token: str
    token_type: Literal["Bearer"]
    expires_in: int
    scope: str

class GoogleAuthState(TypedDict):
    """Google OAuth state parameters"""
    state: str
    redirect_uri: str
    scope: str
    response_type: Literal["code"]
    client_id: str
    access_type: NotRequired[Literal["offline"]]
    prompt: NotRequired[Literal["consent"]]

# ========================================
# Stripe Types
# ========================================

class StripeCustomer(TypedDict):
    """Stripe customer object"""
    id: str
    object: Literal["customer"]
    created: int
    email: str
    name: NotRequired[str]
    phone: NotRequired[str]
    description: NotRequired[str]
    metadata: dict[str, str]
    default_source: NotRequired[str]
    invoice_prefix: NotRequired[str]
    currency: NotRequired[str]
    balance: int
    delinquent: bool
    livemode: bool

class StripeSubscription(TypedDict):
    """Stripe subscription object"""
    id: str
    object: Literal["subscription"]
    created: int
    current_period_end: int
    current_period_start: int
    customer: str
    status: Literal["active", "past_due", "unpaid", "canceled", "incomplete", "incomplete_expired", "trialing"]
    plan: dict[str, JSONValue]
    items: dict[str, JSONValue]
    metadata: dict[str, str]
    trial_end: NotRequired[int]
    trial_start: NotRequired[int]
    cancel_at: NotRequired[int]
    canceled_at: NotRequired[int]
    ended_at: NotRequired[int]

class StripePrice(TypedDict):
    """Stripe price object"""
    id: str
    object: Literal["price"]
    active: bool
    created: int
    currency: str
    metadata: dict[str, str]
    nickname: NotRequired[str]
    product: str
    recurring: NotRequired[dict[str, JSONValue]]
    type: Literal["one_time", "recurring"]
    unit_amount: int
    unit_amount_decimal: str

class StripeProduct(TypedDict):
    """Stripe product object"""
    id: str
    object: Literal["product"]
    active: bool
    created: int
    description: NotRequired[str]
    images: list[str]
    metadata: dict[str, str]
    name: str
    statement_descriptor: NotRequired[str]
    type: Literal["service", "good"]
    updated: int
    url: NotRequired[str]

class StripeBillingPortalSession(TypedDict):
    """Stripe billing portal session"""
    id: str
    object: Literal["billing_portal.session"]
    created: int
    customer: str
    livemode: bool
    return_url: str
    url: str

class StripeCheckoutSession(TypedDict):
    """Stripe checkout session"""
    id: str
    object: Literal["checkout.session"]
    created: int
    customer: NotRequired[str]
    customer_email: NotRequired[str]
    mode: Literal["payment", "setup", "subscription"]
    payment_status: Literal["paid", "unpaid", "no_payment_required"]
    status: Literal["open", "complete", "expired"]
    success_url: str
    cancel_url: str
    url: str
    metadata: dict[str, str]

class StripeWebhookEvent(TypedDict):
    """Stripe webhook event"""
    id: str
    object: Literal["event"]
    api_version: str
    created: int
    data: dict[str, JSONValue]
    livemode: bool
    pending_webhooks: int
    request: NotRequired[dict[str, JSONValue]]
    type: str

# ========================================
# AWS Lambda Types (External Context)
# ========================================

class LambdaContext(TypedDict):
    """AWS Lambda context object (approximation)"""
    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: str
    remaining_time_in_millis: int
    log_group_name: str
    log_stream_name: str
    aws_request_id: str

class APIGatewayProxyEvent(TypedDict):
    """AWS API Gateway proxy event"""
    resource: str
    path: str
    httpMethod: str
    headers: dict[str, str]
    multiValueHeaders: dict[str, list[str]]
    queryStringParameters: NotRequired[dict[str, str]]
    multiValueQueryStringParameters: NotRequired[dict[str, list[str]]]
    pathParameters: NotRequired[dict[str, str]]
    stageVariables: NotRequired[dict[str, str]]
    requestContext: dict[str, JSONValue]
    body: NotRequired[str]
    isBase64Encoded: bool

class APIGatewayProxyResponse(TypedDict):
    """AWS API Gateway proxy response"""
    statusCode: int
    headers: NotRequired[dict[str, str]]
    multiValueHeaders: NotRequired[dict[str, list[str]]]
    body: str
    isBase64Encoded: NotRequired[bool]

# ========================================
# OAuth Provider Types (Generic)
# ========================================

class OAuthTokenResponse(TypedDict):
    """Generic OAuth token response"""
    access_token: str
    token_type: str
    refresh_token: NotRequired[str]
    expires_in: NotRequired[int]
    scope: NotRequired[str]
    id_token: NotRequired[str]

class OAuthUserProfile(TypedDict):
    """Generic OAuth user profile"""
    id: str
    email: str
    name: str
    picture: NotRequired[str]
    verified_email: NotRequired[bool]
    locale: NotRequired[str]

class OAuthError(TypedDict):
    """OAuth error response"""
    error: str
    error_description: NotRequired[str]
    error_uri: NotRequired[str]

# ========================================
# HTTP Request/Response Types
# ========================================

class HTTPHeaders(TypedDict, total=False):
    """Common HTTP headers"""
    Authorization: str
    Content_Type: str
    Accept: str
    User_Agent: str
    Cache_Control: str
    X_Forwarded_For: str
    X_Real_IP: str
    Origin: str
    Referer: str

class CORSHeaders(TypedDict, total=False):
    """CORS-specific headers"""
    Access_Control_Allow_Origin: str
    Access_Control_Allow_Methods: str
    Access_Control_Allow_Headers: str
    Access_Control_Allow_Credentials: str
    Access_Control_Max_Age: str

# ========================================
# Third-Party Integration Responses
# ========================================

class ExternalAPIError(TypedDict):
    """Standardized external API error"""
    code: str
    message: str
    details: NotRequired[dict[str, JSONValue]]
    timestamp: ISODateString
    request_id: NotRequired[str]

class ExternalAPISuccess(TypedDict):
    """Standardized external API success response"""
    data: JSONValue
    timestamp: ISODateString
    request_id: NotRequired[str]
    metadata: NotRequired[dict[str, JSONValue]]
