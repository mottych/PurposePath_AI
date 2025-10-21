"""Shared data access layer for cross-module communication in PurposePath."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar, cast

import structlog
from boto3.dynamodb.conditions import And, Attr, ConditionBase, Key
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

# Import shared types for enhanced type safety
from shared.types import (
    BusinessDataGetResult,
    UserCreateResult,
    UserGetResult,
    create_user_id,
)

# Import coaching models for proper typing
from shared.types.coaching_models import CoachingSession as CoachingSessionDict
from shared.types.coaching_models import SessionCreateData, SessionUpdateData
from shared.types.coaching_models import UserPreferences as UserPreferencesDict
from shared.types.common import JSONDict

from ..models.multitenant import (
    BusinessData,
    CoachingSession,
    CoachingTopic,
    Invitation,
    InvitationStatus,
    RequestContext,
    Subscription,
    Tenant,
    TenantStatus,
    User,
    UserPreferences,
    UserRole,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T")

# Type aliases for data access patterns
DynamoDBItem = JSONDict
BusinessFieldValue = (
    str | int | float | bool | list[object] | dict[str, object]
)  # Valid business field types
ContextOrTable = str | RequestContext | None  # Table name string or RequestContext object


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with tenant isolation."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        """Initialize repository with DynamoDB table."""
        # Use aws_helpers for proper typing
        from .aws_helpers import get_dynamodb_resource

        self.dynamodb: DynamoDBServiceResource = get_dynamodb_resource(region)
        # DynamoDB.Table() return type needs explicit annotation for proper typing
        self.table: Table = self.dynamodb.Table(table_name)
        self.table_name = table_name

    @abstractmethod
    def _item_to_model(self, item: DynamoDBItem) -> T:
        """Convert DynamoDB item to domain model."""
        pass

    @abstractmethod
    def _model_to_item(self, model: T) -> DynamoDBItem:
        """Convert domain model to DynamoDB item."""
        pass

    def _ensure_tenant_isolation(self, context: RequestContext, item: DynamoDBItem) -> DynamoDBItem:
        """Ensure tenant isolation by adding tenant_id filter."""
        if "tenant_id" in item and item["tenant_id"] != context.tenant_id:
            raise PermissionError("Access denied: tenant mismatch")
        return item


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant data management."""

    def _item_to_model(self, item: DynamoDBItem) -> Tenant:
        """Convert DynamoDB item to Tenant model."""
        # Convert JSONValue dict to proper types for Pydantic
        converted_item = cast(dict[str, Any], item)
        return Tenant(**converted_item)

    def _model_to_item(self, model: Tenant) -> DynamoDBItem:
        """Convert Tenant model to DynamoDB item."""
        return model.model_dump()

    def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        item = self._model_to_item(tenant)

        try:
            # Cast to Any for boto3 compatibility
            self.table.put_item(
                Item=cast(dict[str, Any], item), ConditionExpression=Attr("tenant_id").not_exists()
            )
            logger.info("Tenant created", tenant_id=tenant.tenant_id, name=tenant.name)
            return tenant
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise ValueError(f"Tenant with ID {tenant.tenant_id} already exists") from e
            raise

    def get_by_id(self, tenant_id: str) -> Tenant | None:
        """Get tenant by ID."""
        try:
            response = self.table.get_item(Key={"tenant_id": tenant_id})
            if "Item" in response:
                # Cast from boto3's Any to our type
                return self._item_to_model(cast(DynamoDBItem, response["Item"]))
            return None
        except ClientError as e:
            logger.error("Failed to get tenant", tenant_id=tenant_id, error=str(e))
            raise

    def get_by_domain(self, domain: str) -> Tenant | None:
        """Get tenant by domain name."""
        try:
            # Assuming GSI on domain
            response = self.table.query(
                IndexName="domain-index", KeyConditionExpression=Key("domain").eq(domain)
            )
            items = response.get("Items", [])
            if items:
                # Cast from boto3's Any to our type
                return self._item_to_model(cast(DynamoDBItem, items[0]))
            return None
        except ClientError as e:
            logger.error("Failed to get tenant by domain", domain=domain, error=str(e))
            raise

    def update_status(self, tenant_id: str, status: TenantStatus, updated_by: str) -> bool:
        """Update tenant status."""
        try:
            _ = self.table.update_item(
                Key={"tenant_id": tenant_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at, updated_by = :updated_by",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": status,
                    ":updated_at": datetime.now(UTC).isoformat(),
                    ":updated_by": updated_by,
                },
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error("Failed to update tenant status", tenant_id=tenant_id, error=str(e))
            return False


class UserRepository(BaseRepository[User]):
    """Repository for user data management with tenant isolation."""

    def _item_to_model(self, item: DynamoDBItem) -> User:
        """Convert DynamoDB item to User model."""
        # Convert JSONValue dict to proper types for Pydantic
        converted_item = cast(dict[str, Any], item)
        return User(**converted_item)

    def _model_to_item(self, model: User) -> DynamoDBItem:
        """Convert User model to DynamoDB item."""
        return model.model_dump()

    def create(self, context: RequestContext, user: User) -> User:
        """Create a new user in the tenant."""
        user.tenant_id = context.tenant_id  # Ensure tenant isolation
        item = self._model_to_item(user)

        try:
            self.table.put_item(
                Item=cast(dict[str, Any], item), ConditionExpression=Attr("user_id").not_exists()
            )
            logger.info("User created", user_id=user.user_id, tenant_id=context.tenant_id)
            return user
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise ValueError(f"User with ID {user.user_id} already exists") from e
            raise

    def create_typed(self, context: RequestContext, user: User) -> UserCreateResult:
        """Create a new user with typed result."""
        try:
            user.tenant_id = context.tenant_id
            item = self._model_to_item(user)

            self.table.put_item(
                Item=cast(dict[str, Any], item), ConditionExpression=Attr("user_id").not_exists()
            )

            logger.info("User created", user_id=user.user_id, tenant_id=context.tenant_id)
            return {
                "success": True,
                "user_id": create_user_id(user.user_id),
                # Note: 'user' field omitted for now - would need full DynamoDB type conversion
            }
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return {
                    "success": False,
                    "error": f"User with ID {user.user_id} already exists",
                    "error_code": "USER_EXISTS",
                }
            return {
                "success": False,
                "error": f"Failed to create user: {e!s}",
                "error_code": "CREATE_FAILED",
            }

    def get_by_id(self, context: RequestContext, user_id: str) -> User | None:
        """Get user by ID with tenant isolation."""
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                item = self._ensure_tenant_isolation(context, cast(DynamoDBItem, response["Item"]))
                return self._item_to_model(item)
            return None
        except ClientError as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            raise

    def get_by_id_typed(self, context: RequestContext, user_id: str) -> UserGetResult:
        """Get user by ID with typed result."""
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                item = self._ensure_tenant_isolation(context, cast(DynamoDBItem, response["Item"]))
                user = self._item_to_model(item)
                logger.info("User found", user_id=user.user_id)
                return {"success": True, "found": True}
            return {
                "success": False,
                "found": False,
                "error": "User not found",
                "error_code": "USER_NOT_FOUND",
            }
        except ClientError as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            return {
                "success": False,
                "found": False,
                "error": f"Failed to get user: {e!s}",
                "error_code": "GET_FAILED",
            }

    def get_by_email(self, context: RequestContext, email: str) -> User | None:
        """Get user by email with tenant isolation."""
        try:
            # Assuming GSI on email
            response = self.table.query(
                IndexName="email-index",
                KeyConditionExpression=Key("email").eq(email),
                FilterExpression=Attr("tenant_id").eq(context.tenant_id),
            )
            if response["Items"]:
                return self._item_to_model(cast(DynamoDBItem, response["Items"][0]))
            return None
        except ClientError as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            raise

    def list_by_tenant(self, context: RequestContext) -> list[User]:
        """List all users in a tenant."""
        try:
            response = self.table.query(
                IndexName="tenant-index",
                KeyConditionExpression=Key("tenant_id").eq(context.tenant_id),
            )
            return [
                self._item_to_model(cast(DynamoDBItem, item)) for item in response.get("Items", [])
            ]
        except ClientError as e:
            logger.error("Failed to list users", tenant_id=context.tenant_id, error=str(e))
            raise

    def update_role(self, context: RequestContext, user_id: str, role: UserRole) -> bool:
        """Update user role with tenant isolation."""
        try:
            # First verify the user belongs to the tenant
            user = self.get_by_id(context, user_id)
            if not user:
                return False

            _ = self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET #role = :role, updated_at = :updated_at",
                ExpressionAttributeNames={"#role": "role"},
                ExpressionAttributeValues={
                    ":role": role.value,
                    ":updated_at": datetime.now(UTC).isoformat(),
                },
                ConditionExpression=Attr("tenant_id").eq(context.tenant_id),
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error("Failed to update user role", user_id=user_id, error=str(e))
            return False


class BusinessDataRepository(BaseRepository[BusinessData]):
    """Repository for business data management with tenant isolation."""

    def __init__(self, context_or_table: ContextOrTable = None, region: str = "us-east-1"):
        """Initialize with flexible context/table parameter."""
        if isinstance(context_or_table, RequestContext):
            # Initialize with context
            super().__init__("purposepath-business-data-dev", region)
            self.context: RequestContext | None = context_or_table
        elif isinstance(context_or_table, str):
            # Initialize with table name
            super().__init__(context_or_table, region)
            self.context = None
        else:
            # Default initialization
            super().__init__("purposepath-business-data-dev", region)
            self.context = None

    def _item_to_model(self, item: DynamoDBItem) -> BusinessData:
        """Convert DynamoDB item to BusinessData model."""
        # Convert JSONValue dict to proper types for Pydantic
        converted_item = cast(dict[str, Any], item)
        return BusinessData(**converted_item)

    def _model_to_item(self, model: BusinessData) -> DynamoDBItem:
        """Convert BusinessData model to DynamoDB item."""
        return model.model_dump()

    def get_by_tenant(self) -> BusinessData | None:
        """Get business data for tenant from context."""
        if not self.context:
            raise ValueError("Context required for tenant-based operations")

        try:
            response = self.table.get_item(Key={"tenant_id": self.context.tenant_id})
            if "Item" in response:
                return self._item_to_model(cast(DynamoDBItem, response["Item"]))
            return None
        except ClientError as e:
            logger.error(
                "Failed to get business data", tenant_id=self.context.tenant_id, error=str(e)
            )
            raise

    def get_by_tenant_typed(self) -> BusinessDataGetResult:
        """Get business data with typed result."""
        if not self.context:
            return {
                "success": False,
                "found": False,
                "error": "Context required for tenant operations",
                "error_code": "NO_CONTEXT",
            }

        try:
            response = self.table.get_item(Key={"tenant_id": self.context.tenant_id})
            if "Item" in response:
                business_data = self._item_to_model(cast(DynamoDBItem, response["Item"]))
                logger.info(
                    "Business data found",
                    tenant_id=self.context.tenant_id,
                    version=business_data.version,
                )
                return {"success": True, "found": True}
            return {
                "success": False,
                "found": False,
                "error": "Business data not found",
                "error_code": "DATA_NOT_FOUND",
            }
        except ClientError as e:
            logger.error(
                "Failed to get business data", tenant_id=self.context.tenant_id, error=str(e)
            )
            return {
                "success": False,
                "found": False,
                "error": f"Failed to get business data: {e!s}",
                "error_code": "GET_FAILED",
            }

    def create_or_update(self, business_data: BusinessData) -> BusinessData:
        """Create or update business data."""
        if not self.context:
            raise ValueError("Context required for tenant-based operations")

        business_data.tenant_id = self.context.tenant_id
        item = self._model_to_item(business_data)

        try:
            self.table.put_item(Item=cast(dict[str, Any], item))
            logger.info("Business data updated", tenant_id=self.context.tenant_id)
            return business_data
        except ClientError as e:
            logger.error(
                "Failed to update business data", tenant_id=self.context.tenant_id, error=str(e)
            )
            raise

    def update_field(self, field: str, value: BusinessFieldValue, updated_by: str) -> bool:
        """Update a specific business data field."""
        if not self.context:
            raise ValueError("Context required for tenant-based operations")

        try:
            # Get current data for change history
            current_data = self.get_by_tenant()
            previous_value = getattr(current_data, field, None) if current_data else None

            # Create change history entry
            change_entry: dict[str, Any] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "user_id": updated_by,
                "field": field,
                "previous_value": previous_value,
                "new_value": value,
                "source": "direct_update",
            }

            # Update the field and add to change history
            update_expr = (
                f"SET #{field} = :value, updated_at = :updated_at, updated_by = :updated_by"
            )
            expr_attr_names = {f"#{field}": field}
            expr_attr_values: dict[str, Any] = {
                ":value": value,
                ":updated_at": datetime.now(UTC).isoformat(),
                ":updated_by": updated_by,
            }

            # Add change history if current data exists
            if current_data and hasattr(current_data, "change_history"):
                update_expr += ", change_history = list_append(if_not_exists(change_history, :empty_list), :change_entry)"
                expr_attr_values[":change_entry"] = [change_entry]
                expr_attr_values[":empty_list"] = []

            _ = self.table.update_item(
                Key={"tenant_id": self.context.tenant_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error("Failed to update business data field", field=field, error=str(e))
            return False

    def update_business_data(self, tenant_id: str, update_data: dict[str, Any]) -> bool:
        """Update business data with change tracking."""
        try:
            # Get current data for change history
            response = self.table.get_item(Key={"tenant_id": tenant_id})
            current_data: dict[str, Any] = response.get("Item", {}) if "Item" in response else {}

            # Create change history entry
            change_entry: dict[str, Any] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "user_id": update_data.get("last_updated_by", "system"),
                "fields_changed": list(update_data.keys()),
                "source": "business_update",
                "version": update_data.get("version", "1.0"),
            }

            # Build update expression
            update_expr_parts: list[str] = []
            expr_attr_values: dict[str, Any] = {}

            for key, value in update_data.items():
                if key not in ["change_history"]:  # Handle change_history separately
                    update_expr_parts.append(f"{key} = :{key}")
                    expr_attr_values[f":{key}"] = value

            # Add change history
            if current_data:
                update_expr_parts.append(
                    "change_history = list_append(if_not_exists(change_history, :empty_list), :change_entry)"
                )
                expr_attr_values[":change_entry"] = [change_entry]
                expr_attr_values[":empty_list"] = []

            update_expr = "SET " + ", ".join(update_expr_parts)

            _ = self.table.update_item(
                Key={"tenant_id": tenant_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error("Failed to update business data", tenant_id=tenant_id, error=str(e))
            return False


class CoachingSessionRepository(BaseRepository[CoachingSession]):
    """Repository for coaching session management with tenant isolation."""

    def __init__(self, context_or_table: ContextOrTable = None, region: str = "us-east-1"):
        """Initialize with flexible context/table parameter."""
        if isinstance(context_or_table, RequestContext):
            # Initialize with context
            super().__init__("purposepath-coaching-sessions-dev", region)
            self.context: RequestContext | None = context_or_table
        elif isinstance(context_or_table, str):
            # Initialize with table name
            super().__init__(context_or_table, region)
            self.context = None
        else:
            # Default initialization
            super().__init__("purposepath-coaching-sessions-dev", region)
            self.context = None

    def _item_to_model(self, item: DynamoDBItem) -> CoachingSession:
        """Convert DynamoDB item to CoachingSession model."""
        # Convert JSONValue dict to proper types for Pydantic
        converted_item = cast(dict[str, Any], item)
        return CoachingSession(**converted_item)

    def _model_to_item(self, model: CoachingSession) -> DynamoDBItem:
        """Convert CoachingSession model to DynamoDB item."""
        return model.model_dump()

    def create(self, session_data: SessionCreateData) -> CoachingSessionDict:
        """Create a new coaching session with proper typing."""
        try:
            # Ensure tenant isolation if context is available
            if self.context:
                session_data["tenant_id"] = self.context.tenant_id

            self.table.put_item(
                Item=cast(dict[str, Any], session_data),
                ConditionExpression=Attr("session_id").not_exists(),
            )
            logger.info("Coaching session created", session_id=session_data["session_id"])
            return cast(CoachingSessionDict, session_data)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise ValueError(
                    f"Session with ID {session_data['session_id']} already exists"
                ) from e
            raise

    def get_by_id(self, session_id: str) -> CoachingSessionDict | None:
        """Get coaching session by ID with proper typing."""
        try:
            response = self.table.get_item(Key={"session_id": session_id})
            if "Item" in response:
                # If we have context, ensure tenant isolation
                if self.context:
                    item = self._ensure_tenant_isolation(
                        self.context, cast(DynamoDBItem, response["Item"])
                    )
                    return cast(CoachingSessionDict, item)
                return cast(CoachingSessionDict, response["Item"])
            return None
        except ClientError as e:
            logger.error("Failed to get coaching session", session_id=session_id, error=str(e))
            return None

    def get_by_id_full(self, context: RequestContext, session_id: str) -> CoachingSession | None:
        """Get coaching session by ID (full domain model)."""
        try:
            response = self.table.get_item(Key={"session_id": session_id})
            if "Item" in response:
                item = self._ensure_tenant_isolation(context, cast(DynamoDBItem, response["Item"]))
                session = self._item_to_model(item)
                # Additional check for user access (unless admin)
                if session.user_id != context.user_id and not self._can_view_all_sessions(context):
                    raise PermissionError("Access denied to this coaching session")
                return session
            return None
        except ClientError as e:
            logger.error("Failed to get coaching session", session_id=session_id, error=str(e))
            raise

    def get_active_session_by_topic(
        self, context: RequestContext, topic: CoachingTopic
    ) -> CoachingSession | None:
        """Get active coaching session for a user and topic."""
        try:
            # Query by user and topic, filter by status = 'active'
            response = self.table.query(
                IndexName="user-topic-index",
                KeyConditionExpression=Key("user_id").eq(context.user_id) & Key("topic").eq(topic),
                FilterExpression=Attr("status").eq("active")
                & Attr("tenant_id").eq(context.tenant_id),
            )
            if response["Items"]:
                return self._item_to_model(cast(DynamoDBItem, response["Items"][0]))
            return None
        except ClientError as e:
            logger.error(
                "Failed to get active session", user_id=context.user_id, topic=topic, error=str(e)
            )
            return None

    def complete_session(
        self, context: RequestContext, session_id: str, outcomes: dict[str, Any]
    ) -> bool:
        """Complete a coaching session with outcomes."""
        try:
            # Verify session belongs to user/tenant
            session = self.get_by_id_full(context, session_id)
            if not session:
                return False

            _ = self.table.update_item(
                Key={"session_id": session_id},
                UpdateExpression="SET #status = :status, outcomes = :outcomes, completed_at = :completed_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "completed",
                    ":outcomes": outcomes,
                    ":completed_at": datetime.now(UTC).isoformat(),
                },
                ConditionExpression=Attr("tenant_id").eq(context.tenant_id),
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error("Failed to complete session", session_id=session_id, error=str(e))
            return False

    def update(self, session_id: str, update_data: SessionUpdateData) -> bool:
        """Update coaching session with typed data."""
        try:
            # Build update expression dynamically
            update_expr_parts: list[str] = []
            expr_attr_values: dict[str, Any] = {}

            for key, value in update_data.items():
                update_expr_parts.append(f"{key} = :{key}")
                expr_attr_values[f":{key}"] = value

            if not update_expr_parts:
                return True  # Nothing to update

            update_expr = "SET " + ", ".join(update_expr_parts)

            _ = self.table.update_item(
                Key={"session_id": session_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error("Failed to update session", session_id=session_id, error=str(e))
            return False

    def get_by_user_and_topic(self, user_id: str, topic: str) -> list[CoachingSessionDict]:
        """Get sessions by user and topic with proper typing."""
        try:
            # Build filter expression
            filter_expr = Key("user_id").eq(user_id) & Key("topic").eq(topic)

            # Add tenant filter if context available
            if self.context:
                filter_expr = filter_expr & Attr("tenant_id").eq(self.context.tenant_id)

            response = self.table.query(
                IndexName="user-topic-index", KeyConditionExpression=filter_expr
            )
            return cast(list[CoachingSessionDict], response.get("Items", []))
        except ClientError as e:
            logger.error(
                "Failed to get sessions by user and topic",
                user_id=user_id,
                topic=topic,
                error=str(e),
            )
            return []

    def _can_view_all_sessions(self, _context: RequestContext) -> bool:
        """Check if user can view all sessions (admin check)."""
        # This would typically check user role from context
        # For now, simple implementation - would need to add user_role to RequestContext
        return False  # Default to false for security


class InvitationRepository(BaseRepository[Invitation]):
    """Repository for invitation management."""

    def _item_to_model(self, item: DynamoDBItem) -> Invitation:
        """Convert DynamoDB item to Invitation model."""
        # Convert JSONValue types properly
        expires_at_str = str(item.get("expires_at", datetime.now(UTC).isoformat()))
        accepted_at_val = item.get("accepted_at")
        accepted_at = datetime.fromisoformat(str(accepted_at_val)) if accepted_at_val else None
        email_sent_at_val = item.get("email_sent_at")
        email_sent_at = (
            datetime.fromisoformat(str(email_sent_at_val)) if email_sent_at_val else None
        )
        message_val = item.get("message")
        message = str(message_val) if message_val is not None else None
        accepted_user_id_val = item.get("accepted_user_id")
        accepted_user_id = str(accepted_user_id_val) if accepted_user_id_val is not None else None

        return Invitation(
            invitation_id=str(item.get("invitation_id", "")),
            tenant_id=str(item.get("tenant_id", "")),
            email=str(item.get("email", "")),
            invited_by_user_id=str(item.get("invited_by_user_id", "")),
            role=UserRole(item.get("role", UserRole.MEMBER.value)),
            status=InvitationStatus(item.get("status", InvitationStatus.PENDING.value)),
            expires_at=datetime.fromisoformat(expires_at_str),
            accepted_at=accepted_at,
            message=message,
            email_sent_at=email_sent_at,
            accepted_user_id=accepted_user_id,
        )

    def _model_to_item(self, model: Invitation) -> DynamoDBItem:
        """Convert Invitation model to DynamoDB item."""
        item = model.model_dump()
        # Convert datetime objects to ISO strings for DynamoDB
        for field in ["invited_at", "expires_at", "accepted_at"]:
            if item.get(field) and isinstance(item[field], datetime):
                item[field] = item[field].isoformat()
        return item

    def create(self, context: RequestContext, invitation: Invitation) -> Invitation:
        """Create a new invitation."""
        invitation.tenant_id = context.tenant_id  # Ensure tenant isolation
        item = self._model_to_item(invitation)

        try:
            self.table.put_item(
                Item=cast(dict[str, Any], item),
                ConditionExpression=Attr("invitation_id").not_exists(),
            )
            logger.info(
                "Invitation created", invitation_id=invitation.invitation_id, email=invitation.email
            )
            return invitation
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise ValueError(
                    f"Invitation with ID {invitation.invitation_id} already exists"
                ) from e
            raise

    def get_by_id(self, context: RequestContext, invitation_id: str) -> Invitation | None:
        """Get invitation by ID with tenant isolation."""
        try:
            response = self.table.get_item(Key={"invitation_id": invitation_id})
            if "Item" in response:
                item = self._ensure_tenant_isolation(context, cast(DynamoDBItem, response["Item"]))
                return self._item_to_model(item)
            return None
        except ClientError as e:
            logger.error("Failed to get invitation", invitation_id=invitation_id, error=str(e))
            raise

    def list_by_tenant(
        self, context: RequestContext, status: InvitationStatus | None = None
    ) -> list[Invitation]:
        """List invitations by tenant with optional status filter."""
        try:
            filter_expr: ConditionBase = Attr("tenant_id").eq(context.tenant_id)
            if status:
                status_condition = Attr("status").eq(status.value)
                # Use And to properly combine conditions
                filter_expr = And(filter_expr, status_condition)

            response = self.table.scan(FilterExpression=filter_expr)
            return [
                self._item_to_model(cast(DynamoDBItem, item)) for item in response.get("Items", [])
            ]
        except ClientError as e:
            logger.error("Failed to list invitations", tenant_id=context.tenant_id, error=str(e))
            raise

    def update_status(
        self, context: RequestContext, invitation_id: str, status: InvitationStatus
    ) -> bool:
        """Update invitation status."""
        try:
            update_expr = "SET #status = :status, updated_at = :updated_at"
            expr_attr_names = {"#status": "status"}
            expr_attr_values = {
                ":status": status.value,
                ":updated_at": datetime.now(UTC).isoformat(),
            }

            if status == InvitationStatus.ACCEPTED:
                update_expr += ", accepted_at = :accepted_at"
                expr_attr_values[":accepted_at"] = datetime.now(UTC).isoformat()

            _ = self.table.update_item(
                Key={"invitation_id": invitation_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ConditionExpression=Attr("tenant_id").eq(context.tenant_id),
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error(
                "Failed to update invitation status", invitation_id=invitation_id, error=str(e)
            )
            return False


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for subscription management."""

    def _item_to_model(self, item: DynamoDBItem) -> Subscription:
        """Convert DynamoDB item to Subscription model."""
        # Convert JSONValue dict to proper types for Pydantic
        converted_item = cast(dict[str, Any], item)
        return Subscription(**converted_item)

    def _model_to_item(self, model: Subscription) -> DynamoDBItem:
        """Convert Subscription model to DynamoDB item."""
        return model.model_dump()

    def create(self, context: RequestContext, subscription: Subscription) -> Subscription:
        """Create a new subscription."""
        subscription.tenant_id = context.tenant_id  # Ensure tenant isolation
        item = self._model_to_item(subscription)

        try:
            self.table.put_item(
                Item=cast(dict[str, Any], item),
                ConditionExpression=Attr("subscription_id").not_exists(),
            )
            logger.info(
                "Subscription created",
                subscription_id=subscription.subscription_id,
                tenant_id=context.tenant_id,
            )
            return subscription
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise ValueError(
                    f"Subscription with ID {subscription.subscription_id} already exists"
                ) from e
            raise

    def get_by_tenant(self, context: RequestContext) -> Subscription | None:
        """Get active subscription for tenant."""
        try:
            response = self.table.query(
                IndexName="tenant-index",
                KeyConditionExpression=Key("tenant_id").eq(context.tenant_id),
                FilterExpression=Attr("status").eq("active"),
            )
            if response["Items"]:
                return self._item_to_model(cast(DynamoDBItem, response["Items"][0]))
            return None
        except ClientError as e:
            logger.error("Failed to get subscription", tenant_id=context.tenant_id, error=str(e))
            raise

    def update_status(self, context: RequestContext, subscription_id: str, status: str) -> bool:
        """Update subscription status."""
        try:
            _ = self.table.update_item(
                Key={"subscription_id": subscription_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": status,
                    ":updated_at": datetime.now(UTC).isoformat(),
                },
                ConditionExpression=Attr("tenant_id").eq(context.tenant_id),
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error(
                "Failed to update subscription status",
                subscription_id=subscription_id,
                error=str(e),
            )
            return False


class UserPreferencesRepository(BaseRepository[UserPreferences]):
    """Repository for user preferences management with tenant isolation."""

    def _item_to_model(self, item: DynamoDBItem) -> UserPreferences:
        """Convert DynamoDB item to UserPreferences model."""
        # Convert JSONValue dict to proper types for Pydantic
        converted_item = cast(dict[str, Any], item)
        return UserPreferences(**converted_item)

    def _model_to_item(self, model: UserPreferences) -> DynamoDBItem:
        """Convert UserPreferences model to DynamoDB item."""
        return model.model_dump()

    def create_or_update(
        self, context: RequestContext, preferences: UserPreferences
    ) -> UserPreferences:
        """Create or update user preferences."""
        preferences.user_id = context.user_id
        preferences.tenant_id = context.tenant_id
        item = self._model_to_item(preferences)

        try:
            self.table.put_item(Item=cast(dict[str, Any], item))
            logger.info(
                "User preferences updated", user_id=context.user_id, tenant_id=context.tenant_id
            )
            return preferences
        except ClientError as e:
            logger.error("Failed to update user preferences", user_id=context.user_id, error=str(e))
            raise

    def get_by_user_id(self, user_id: str) -> UserPreferencesDict | None:
        """Get user preferences by user ID with proper typing."""
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                return cast(UserPreferencesDict, response["Item"])
            return None
        except ClientError as e:
            logger.error("Failed to get user preferences", user_id=user_id, error=str(e))
            return None

    def get_by_user_id_full(self, context: RequestContext, user_id: str) -> UserPreferences | None:
        """Get user preferences by user ID (full domain model)."""
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                item = self._ensure_tenant_isolation(context, cast(DynamoDBItem, response["Item"]))
                return self._item_to_model(item)
            return None
        except ClientError as e:
            logger.error("Failed to get user preferences", user_id=user_id, error=str(e))
            raise

    def update_coaching_preferences(
        self, context: RequestContext, preferences: dict[str, Any]
    ) -> bool:
        """Update coaching-specific preferences."""
        try:
            _ = self.table.update_item(
                Key={"user_id": context.user_id},
                UpdateExpression="SET coaching_preferences = :prefs, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ":prefs": preferences,
                    ":updated_at": datetime.now(UTC).isoformat(),
                },
                ConditionExpression=Attr("tenant_id").eq(context.tenant_id),
                ReturnValues="UPDATED_NEW",
            )
            return True
        except ClientError as e:
            logger.error(
                "Failed to update coaching preferences", user_id=context.user_id, error=str(e)
            )
            return False
