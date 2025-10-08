"""Shared data access layer for cross-module communication in PurposePath."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar, cast

import structlog
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table
from shared.services.aws_helpers import get_dynamodb_resource

from shared.models.multitenant import (
    BusinessData,
    CoachingSession,
    CoachingTopic,
    Invitation,
    InvitationStatus,
    RequestContext,
    Subscription,
    SubscriptionTier,
    Tenant,
    TenantStatus,
    User,
    UserPreferences,
    UserRole,
)

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with tenant isolation."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        """Initialize repository with DynamoDB table."""
        self.dynamodb: DynamoDBServiceResource = get_dynamodb_resource(region)
        self.table: Table = self.dynamodb.Table(table_name)
        self.table_name = table_name

    @abstractmethod
    def _item_to_model(self, item: Dict[str, Any]) -> T:
        """Convert DynamoDB item to domain model."""
        pass

    @abstractmethod
    def _model_to_item(self, model: T) -> Dict[str, Any]:
        """Convert domain model to DynamoDB item."""
        pass

    def _ensure_tenant_isolation(self, context: RequestContext, item: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure tenant isolation by adding tenant_id filter."""
        if 'tenant_id' in item and item['tenant_id'] != context.tenant_id:
            raise PermissionError("Access denied: tenant mismatch")
        return item


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant data management."""

    def _item_to_model(self, item: Dict[str, Any]) -> Tenant:
        """Convert DynamoDB item to Tenant model."""
        return Tenant(**item)

    def _model_to_item(self, model: Tenant) -> Dict[str, Any]:
        """Convert Tenant model to DynamoDB item."""
        return model.model_dump()

    def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        item = self._model_to_item(tenant)

        try:
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('tenant_id').not_exists()
            )
            logger.info("Tenant created", tenant_id=tenant.tenant_id, name=tenant.name)
            return tenant
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Tenant with ID {tenant.tenant_id} already exists")
            raise

    def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        try:
            response = self.table.get_item(Key={'tenant_id': tenant_id})
            if 'Item' in response:
                return self._item_to_model(response['Item'])
            return None
        except ClientError as e:
            logger.error("Failed to get tenant", tenant_id=tenant_id, error=str(e))
            raise

    def get_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain name."""
        try:
            # Assuming GSI on domain
            response = self.table.query(
                IndexName='domain-index',
                KeyConditionExpression=Key('domain').eq(domain)
            )
            if response['Items']:
                return self._item_to_model(response['Items'][0])
            return None
        except ClientError as e:
            logger.error("Failed to get tenant by domain", domain=domain, error=str(e))
            raise

    def update_status(self, tenant_id: str, status: TenantStatus, updated_by: str) -> bool:
        """Update tenant status."""
        try:
            self.table.update_item(
                Key={'tenant_id': tenant_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, updated_by = :updated_by',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': datetime.now(timezone.utc).isoformat(),
                    ':updated_by': updated_by
                },
                ReturnValues='UPDATED_NEW'
            )
            return True
        except ClientError as e:
            logger.error("Failed to update tenant status", tenant_id=tenant_id, error=str(e))
            return False


class UserRepository(BaseRepository[User]):
    """Repository for user data management with tenant isolation."""

    def _item_to_model(self, item: Dict[str, Any]) -> User:
        """Convert DynamoDB item to User model."""
        return User(**item)

    def _model_to_item(self, model: User) -> Dict[str, Any]:
        """Convert User model to DynamoDB item."""
        return model.model_dump()

    def create(self, context: RequestContext, user: User) -> User:
        """Create a new user in the tenant."""
        user.tenant_id = context.tenant_id  # Ensure tenant isolation
        item = self._model_to_item(user)

        try:
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('user_id').not_exists()
            )
            logger.info("User created", user_id=user.user_id, tenant_id=context.tenant_id)
            return user
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"User with ID {user.user_id} already exists")
            raise

    def get_by_id(self, context: RequestContext, user_id: str) -> Optional[User]:
        """Get user by ID with tenant isolation."""
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            if 'Item' in response:
                item = self._ensure_tenant_isolation(context, response['Item'])
                return self._item_to_model(item)
            return None
        except ClientError as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            raise

    def get_by_email(self, context: RequestContext, email: str) -> Optional[User]:
        """Get user by email within tenant."""
        try:
            # Assuming GSI on tenant_id-email
            response = self.table.query(
                IndexName='tenant-email-index',
                KeyConditionExpression=Key('tenant_id').eq(context.tenant_id) & Key('email').eq(email)
            )
            if response['Items']:
                return self._item_to_model(response['Items'][0])
            return None
        except ClientError as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            raise

    def list_by_tenant(self, context: RequestContext, limit: int = 50) -> List[User]:
        """List all users in a tenant."""
        try:
            response = self.table.query(
                IndexName='tenant-index',
                KeyConditionExpression=Key('tenant_id').eq(context.tenant_id),
                Limit=limit
            )
            return [self._item_to_model(item) for item in response['Items']]
        except ClientError as e:
            logger.error("Failed to list users", tenant_id=context.tenant_id, error=str(e))
            raise

    def update_role(self, context: RequestContext, user_id: str, new_role: UserRole) -> bool:
        """Update user role within tenant."""
        try:
            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET #role = :role, updated_at = :updated_at',
                ConditionExpression=Attr('tenant_id').eq(context.tenant_id),
                ExpressionAttributeNames={'#role': 'role'},
                ExpressionAttributeValues={
                    ':role': new_role,
                    ':updated_at': datetime.now(timezone.utc).isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )
            return True
        except ClientError as e:
            logger.error("Failed to update user role", user_id=user_id, error=str(e))
            return False


class BusinessDataRepository(BaseRepository[BusinessData]):
    """Repository for shared business data management."""

    context: Optional[RequestContext]

    def __init__(self, context_or_table: Any = None, region: str = "us-east-1"):
        """Initialize repository with context or table name."""
        if hasattr(context_or_table, 'tenant_id'):
            # Initialize with RequestContext
            table_name = "purposepath-business-data-dev"  # Default table name
            super().__init__(table_name, region)
            self.context = context_or_table
        else:
            # Initialize with table name (backward compatibility)
            table_name = context_or_table or "purposepath-business-data-dev"
            super().__init__(table_name, region)
            self.context = None

    def _item_to_model(self, item: Dict[str, Any]) -> BusinessData:
        """Convert DynamoDB item to BusinessData model."""
        return BusinessData(**item)

    def _model_to_item(self, model: BusinessData) -> Dict[str, Any]:
        """Convert BusinessData model to DynamoDB item."""
        return model.model_dump()

    def get_by_tenant(self, context: Optional[RequestContext] = None) -> Optional[BusinessData]:
        """Get business data for a tenant."""
        # Use stored context if not provided
        if context is None:
            context = self.context

        if not context:
            logger.error("No context available for tenant lookup")
            return None

        try:
            # Business data ID is typically the tenant ID
            response = self.table.get_item(Key={'business_id': context.tenant_id})
            if 'Item' in response:
                item = self._ensure_tenant_isolation(context, response['Item'])
                return self._item_to_model(item)
            return None
        except ClientError as e:
            logger.error("Failed to get business data", tenant_id=context.tenant_id, error=str(e))
            return None

    def create_or_update(self, context: RequestContext, business_data: BusinessData) -> BusinessData:
        """Create or update business data for a tenant."""
        business_data.tenant_id = context.tenant_id
        business_data.business_id = context.tenant_id  # Use tenant_id as business_id
        business_data.updated_at = datetime.now(timezone.utc)

        item = self._model_to_item(business_data)

        try:
            self.table.put_item(Item=item)
            logger.info("Business data updated", tenant_id=context.tenant_id, updated_by=business_data.last_updated_by)
            return business_data
        except ClientError as e:
            logger.error("Failed to update business data", tenant_id=context.tenant_id, error=str(e))
            raise

    def update_field(self, context: RequestContext, field: str, value: Any, updated_by: str) -> bool:
        """Update a specific field in business data."""
        try:
            # Create change history entry
            change_entry = {
                'field': field,
                'value': value,
                'updated_by': updated_by,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'source': 'coaching_session'  # Can be extended for different sources
            }

            self.table.update_item(
                Key={'business_id': context.tenant_id},
                UpdateExpression='SET #field = :value, updated_at = :updated_at, last_updated_by = :updated_by, change_history = list_append(if_not_exists(change_history, :empty_list), :change)',
                ConditionExpression=Attr('tenant_id').eq(context.tenant_id),
                ExpressionAttributeNames={'#field': field},
                ExpressionAttributeValues={
                    ':value': value,
                    ':updated_at': datetime.now(timezone.utc).isoformat(),
                    ':updated_by': updated_by,
                    ':empty_list': [],
                    ':change': [change_entry]
                },
                ReturnValues='UPDATED_NEW'
            )
            return True
        except ClientError as e:
            logger.error("Failed to update business data field", field=field, tenant_id=context.tenant_id, error=str(e))
            return False

    def update_business_data(self, tenant_id: str, update_data: Dict[str, Any]) -> bool:
        """Update business data (simplified interface for coaching service)."""
        try:
            # Build update expression
            update_expr_parts = []
            expr_attr_values = {}
            expr_attr_names = {}

            for key, value in update_data.items():
                if key in ["last_updated_by", "version", "change_history"]:
                    # Handle special fields
                    update_expr_parts.append(f"#{key} = :{key}")
                    expr_attr_names[f"#{key}"] = key
                    expr_attr_values[f":{key}"] = value
                else:
                    # Handle regular fields
                    update_expr_parts.append(f"#{key} = :{key}")
                    expr_attr_names[f"#{key}"] = key
                    expr_attr_values[f":{key}"] = value

            # Add updated_at timestamp
            update_expr_parts.append("#updated_at = :updated_at")
            expr_attr_names["#updated_at"] = "updated_at"
            expr_attr_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

            update_expr = "SET " + ", ".join(update_expr_parts)

            self.table.update_item(
                Key={'business_id': tenant_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='UPDATED_NEW'
            )
            logger.info("Business data updated", tenant_id=tenant_id)
            return True
        except ClientError as e:
            logger.error("Failed to update business data", tenant_id=tenant_id, error=str(e))
            return False


class CoachingSessionRepository(BaseRepository[CoachingSession]):
    """Repository for coaching session management."""

    context: Optional[RequestContext]

    def __init__(self, context_or_table: Any = None, region: str = "us-east-1"):
        """Initialize repository with context or table name."""
        if hasattr(context_or_table, 'tenant_id'):
            # Initialize with RequestContext
            table_name = "purposepath-coaching-sessions-dev"  # Default table name
            super().__init__(table_name, region)
            self.context = context_or_table
        else:
            # Initialize with table name (backward compatibility)
            table_name = context_or_table or "purposepath-coaching-sessions-dev"
            super().__init__(table_name, region)
            self.context = None

    def _item_to_model(self, item: Dict[str, Any]) -> CoachingSession:
        """Convert DynamoDB item to CoachingSession model."""
        return CoachingSession(**item)

    def _model_to_item(self, model: CoachingSession) -> Dict[str, Any]:
        """Convert CoachingSession model to DynamoDB item."""
        return model.model_dump()

    def create(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new coaching session (simplified interface)."""
        try:
            # If initialized with context, use it to ensure tenant isolation
            if self.context:
                session_data["tenant_id"] = self.context.tenant_id

            self.table.put_item(
                Item=session_data,
                ConditionExpression=Attr('session_id').not_exists()
            )
            logger.info("Coaching session created", session_id=session_data.get("session_id"))
            return session_data
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Session with ID {session_data.get('session_id')} already exists")
            raise

    def create_full(self, context: RequestContext, session: CoachingSession) -> CoachingSession:
        """Create a new coaching session (full interface)."""
        session.tenant_id = context.tenant_id
        session.user_id = context.user_id
        item = self._model_to_item(session)

        try:
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('session_id').not_exists()
            )
            logger.info("Coaching session created", session_id=session.session_id, user_id=context.user_id)
            return session
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Session with ID {session.session_id} already exists")
            raise

    def get_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get coaching session by ID (simplified interface)."""
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            if 'Item' in response:
                # If we have context, ensure tenant isolation
                if self.context:
                    item = self._ensure_tenant_isolation(self.context, response['Item'])
                    return item
                return cast(dict[str, Any], response['Item'])
            return None
        except ClientError as e:
            logger.error("Failed to get coaching session", session_id=session_id, error=str(e))
            return None

    def get_by_id_full(self, context: RequestContext, session_id: str) -> Optional[CoachingSession]:
        """Get coaching session by ID (full interface)."""
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            if 'Item' in response:
                item = self._ensure_tenant_isolation(context, response['Item'])
                session = self._item_to_model(item)
                # Additional check for user access (unless admin)
                if session.user_id != context.user_id and not self._can_view_all_sessions(context):
                    raise PermissionError("Access denied to this coaching session")
                return session
            return None
        except ClientError as e:
            logger.error("Failed to get coaching session", session_id=session_id, error=str(e))
            raise

    def get_active_session_by_topic(self, context: RequestContext, topic: CoachingTopic) -> Optional[CoachingSession]:
        """Get active coaching session for a user and topic."""
        try:
            # Query by user and topic, filter by status = 'active'
            response = self.table.query(
                IndexName='user-topic-index',
                KeyConditionExpression=Key('user_id').eq(context.user_id) & Key('topic').eq(topic),
                FilterExpression=Attr('status').eq('active') & Attr('tenant_id').eq(context.tenant_id)
            )
            if response['Items']:
                return self._item_to_model(response['Items'][0])
            return None
        except ClientError as e:
            logger.error("Failed to get active session", user_id=context.user_id, topic=topic, error=str(e))
            raise

    def list_user_sessions(self, context: RequestContext, user_id: Optional[str] = None, limit: int = 50) -> List[CoachingSession]:
        """List coaching sessions for a user."""
        target_user_id = user_id or context.user_id

        # Check permissions for viewing other users' sessions
        if target_user_id != context.user_id and not self._can_view_all_sessions(context):
            raise PermissionError("Access denied to other users' sessions")

        try:
            response = self.table.query(
                IndexName='tenant-user-index',
                KeyConditionExpression=Key('tenant_id').eq(context.tenant_id) & Key('user_id').eq(target_user_id),
                Limit=limit
            )
            return [self._item_to_model(item) for item in response['Items']]
        except ClientError as e:
            logger.error("Failed to list user sessions", user_id=target_user_id, error=str(e))
            raise

    def complete_session(self, context: RequestContext, session_id: str, outcomes: Dict[str, Any]) -> bool:
        """Complete a coaching session and store outcomes."""
        try:
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET #status = :status, outcomes = :outcomes, completed_at = :completed_at, updated_at = :updated_at',
                ConditionExpression=Attr('tenant_id').eq(context.tenant_id) & Attr('user_id').eq(context.user_id),
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':outcomes': outcomes,
                    ':completed_at': datetime.now(timezone.utc).isoformat(),
                    ':updated_at': datetime.now(timezone.utc).isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )
            logger.info("Coaching session completed", session_id=session_id, user_id=context.user_id)
            return True
        except ClientError as e:
            logger.error("Failed to complete session", session_id=session_id, error=str(e))
            return False

    def update(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a coaching session (simplified interface)."""
        try:
            # Build update expression
            update_expr_parts = []
            expr_attr_values = {}

            for key, value in update_data.items():
                update_expr_parts.append(f"#{key} = :{key}")
                expr_attr_values[f":{key}"] = value

            # Add updated_at timestamp
            update_expr_parts.append("#updated_at = :updated_at")
            expr_attr_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

            update_expr = "SET " + ", ".join(update_expr_parts)
            expr_attr_names = {f"#{key}": key for key in update_data.keys()}
            expr_attr_names["#updated_at"] = "updated_at"

            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='UPDATED_NEW'
            )
            logger.info("Coaching session updated", session_id=session_id)
            return True
        except ClientError as e:
            logger.error("Failed to update coaching session", session_id=session_id, error=str(e))
            return False

    def get_by_user_and_topic(self, user_id: str, topic: str) -> List[Dict[str, Any]]:
        """Get sessions by user and topic (simplified interface)."""
        try:
            # If we have context, add tenant filter
            filter_expr = Attr('user_id').eq(user_id) & Attr('topic').eq(topic)
            if self.context:
                filter_expr = filter_expr & Attr('tenant_id').eq(self.context.tenant_id)

            response = self.table.scan(
                FilterExpression=filter_expr
            )
            return cast(list[dict[str, Any]], response.get('Items', []))
        except ClientError as e:
            logger.error("Failed to get sessions by user and topic", user_id=user_id, topic=topic, error=str(e))
            return []

    def _can_view_all_sessions(self, context: RequestContext) -> bool:
        """Check if user can view all sessions in tenant."""
        return context.role in [UserRole.OWNER, UserRole.ADMIN]


class InvitationRepository(BaseRepository[Invitation]):
    """Repository for invitation management."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        super().__init__(table_name, region)

    def _item_to_model(self, item: Dict[str, Any]) -> Invitation:
        """Convert DynamoDB item to Invitation model."""
        from datetime import datetime, timezone

        # Parse datetime fields with proper defaults
        expires_at = item.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        elif expires_at is None:
            expires_at = datetime.now(timezone.utc)

        created_at = item.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        updated_at = item.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc)

        return Invitation(
            invitation_id=item.get('invitation_id') or f"inv_{item.get('token', 'unknown')[:12]}",
            tenant_id=item.get('tenant_id') or "unknown",
            email=item.get('email') or "unknown@example.com",
            role=UserRole(item.get('role', UserRole.MEMBER.value)),
            status=InvitationStatus(item.get('status', InvitationStatus.PENDING.value)),
            invited_by_user_id=item.get('invited_by_user_id') or "unknown",
            token=item.get('token') or "unknown",
            expires_at=expires_at,
            accepted_at=item.get('accepted_at'),
            message=item.get('message'),
            email_sent_at=item.get('email_sent_at'),
            accepted_user_id=item.get('accepted_user_id'),
            created_at=created_at,
            updated_at=updated_at
        )

    def _model_to_item(self, model: Invitation) -> Dict[str, Any]:
        """Convert Invitation model to DynamoDB item."""
        return {
            'invitation_id': model.invitation_id,
            'tenant_id': model.tenant_id,
            'email': model.email,
            'role': model.role.value,
            'status': model.status.value,
            'invited_by_user_id': model.invited_by_user_id,
            'token': model.token,
            'expires_at': model.expires_at,
            'accepted_at': model.accepted_at,
            'message': model.message,
            'email_sent_at': model.email_sent_at,
            'accepted_user_id': model.accepted_user_id,
            'created_at': model.created_at,
            'updated_at': model.updated_at
        }

    def get_by_token(self, token: str) -> Optional[Invitation]:
        """Get invitation by token."""
        try:
            response = self.table.query(
                IndexName='token-index',
                KeyConditionExpression=Key('token').eq(token)
            )
            if response['Items']:
                return self._item_to_model(response['Items'][0])
            return None
        except ClientError as e:
            logger.error("Failed to get invitation by token", error=str(e))
            return None


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for subscription management."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        super().__init__(table_name, region)

    def _item_to_model(self, item: Dict[str, Any]) -> Subscription:
        """Convert DynamoDB item to Subscription model."""
        from datetime import datetime, timezone

        # Parse datetime fields with proper defaults
        def parse_datetime(dt_val: Any) -> datetime:
            if isinstance(dt_val, str):
                return datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
            elif dt_val is None:
                return datetime.now(timezone.utc)
            return cast(datetime, dt_val)

        return Subscription(
            subscription_id=item.get('subscription_id') or f"sub_{item.get('tenant_id', 'unknown')[:12]}",
            tenant_id=item.get('tenant_id') or "unknown",
            tier=SubscriptionTier(item.get('tier', SubscriptionTier.STARTER.value)),
            status=item.get('status', 'active'),
            billing_cycle=item.get('billing_cycle', 'monthly'),
            amount=item.get('amount', 0),
            currency=item.get('currency', 'USD'),
            trial_ends_at=item.get('trial_ends_at'),
            current_period_start=parse_datetime(item.get('current_period_start')),
            current_period_end=parse_datetime(item.get('current_period_end')),
            cancelled_at=item.get('cancelled_at'),
            limits=json.loads(item.get('limits', '{}')),
            usage=json.loads(item.get('usage', '{}')),
            external_subscription_id=item.get('external_subscription_id'),
            created_at=parse_datetime(item.get('created_at')),
            updated_at=parse_datetime(item.get('updated_at'))
        )

    def _model_to_item(self, model: Subscription) -> Dict[str, Any]:
        """Convert Subscription model to DynamoDB item."""
        return {
            'subscription_id': model.subscription_id,
            'tenant_id': model.tenant_id,
            'tier': model.tier.value,
            'status': model.status,
            'billing_cycle': model.billing_cycle,
            'amount': model.amount,
            'currency': model.currency,
            'trial_ends_at': model.trial_ends_at,
            'current_period_start': model.current_period_start,
            'current_period_end': model.current_period_end,
            'cancelled_at': model.cancelled_at,
            'limits': json.dumps(model.limits),
            'usage': json.dumps(model.usage),
            'external_subscription_id': model.external_subscription_id,
            'created_at': model.created_at,
            'updated_at': model.updated_at
        }

    def get_by_tenant(self, tenant_id: str) -> Optional[Subscription]:
        """Get subscription for a tenant."""
        try:
            response = self.table.query(
                IndexName='tenant-index',
                KeyConditionExpression=Key('tenant_id').eq(tenant_id)
            )
            if response['Items']:
                return self._item_to_model(response['Items'][0])
            return None
        except ClientError as e:
            logger.error("Failed to get subscription by tenant", tenant_id=tenant_id, error=str(e))
            return None


class UserPreferencesRepository(BaseRepository[UserPreferences]):
    """Repository for user preferences management."""

    context: Optional[RequestContext]

    def __init__(self, context_or_table: Any = None, region: str = "us-east-1"):
        """Initialize repository with context or table name."""
        if hasattr(context_or_table, 'tenant_id'):
            # Initialize with RequestContext
            table_name = "purposepath-user-preferences-dev"  # Default table name
            super().__init__(table_name, region)
            self.context = context_or_table
        else:
            # Initialize with table name (backward compatibility)
            table_name = context_or_table or "purposepath-user-preferences-dev"
            super().__init__(table_name, region)
            self.context = None

    def _item_to_model(self, item: Dict[str, Any]) -> UserPreferences:
        """Convert DynamoDB item to UserPreferences model."""
        from datetime import datetime, timezone

        # Parse datetime fields with proper defaults
        def parse_datetime(dt_val: Any) -> datetime:
            if isinstance(dt_val, str):
                return datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
            elif dt_val is None:
                return datetime.now(timezone.utc)
            return cast(datetime, dt_val)

        return UserPreferences(
            user_id=item.get('user_id') or "unknown",
            tenant_id=item.get('tenant_id') or "unknown",
            theme=item.get('theme', 'light'),
            language=item.get('language', 'en'),
            timezone=item.get('timezone', 'UTC'),
            date_format=item.get('date_format', 'YYYY-MM-DD'),
            time_format=item.get('time_format', '24h'),
            email_notifications=json.loads(item.get('email_notifications', '{"coaching_reminders": true, "team_updates": true, "system_notifications": true, "marketing": false}')),
            coaching_preferences=json.loads(item.get('coaching_preferences', '{"preferred_session_length": 30, "reminder_frequency": "weekly", "coaching_style": "collaborative"}')),
            dashboard_layout=json.loads(item.get('dashboard_layout', '{}')),
            created_at=parse_datetime(item.get('created_at')),
            updated_at=parse_datetime(item.get('updated_at'))
        )

    def _model_to_item(self, model: UserPreferences) -> Dict[str, Any]:
        """Convert UserPreferences model to DynamoDB item."""
        return {
            'user_id': model.user_id,
            'tenant_id': model.tenant_id,
            'theme': model.theme,
            'language': model.language,
            'timezone': model.timezone,
            'date_format': model.date_format,
            'time_format': model.time_format,
            'email_notifications': json.dumps(model.email_notifications),
            'coaching_preferences': json.dumps(model.coaching_preferences),
            'dashboard_layout': json.dumps(model.dashboard_layout),
            'created_at': model.created_at,
            'updated_at': model.updated_at
        }

    def get_by_user(self, tenant_id: str, user_id: str) -> Optional[UserPreferences]:
        """Get preferences for a user."""
        try:
            response = self.table.query(
                IndexName='user-preferences-index',
                KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('user_id').eq(user_id)
            )
            if response['Items']:
                return self._item_to_model(response['Items'][0])
            return None
        except ClientError as e:
            logger.error("Failed to get user preferences", user_id=user_id, error=str(e))
            return None

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get preferences for a user by user_id only (simplified for coaching service)."""
        try:
            response = self.table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            if response['Items']:
                # Convert to simple dict for coaching service compatibility
                prefs = self._item_to_model(response['Items'][0])
                return prefs.model_dump() if prefs else None
            return None
        except ClientError as e:
            logger.error("Failed to get user preferences by user_id", user_id=user_id, error=str(e))
            return None


# Shared Service Layer

class SharedDataService:
    """Service layer for cross-module data access."""

    def __init__(self, region: str = "us-east-1"):
        """Initialize service with repositories."""
        self.tenant_repo = TenantRepository("purposepath-tenants-dev", region)
        self.user_repo = UserRepository("purposepath-users-dev", region)
        self.business_repo = BusinessDataRepository("purposepath-business-data-dev", region)
        self.session_repo = CoachingSessionRepository("purposepath-coaching-sessions-dev", region)

    def get_tenant_info(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant information."""
        return self.tenant_repo.get_by_id(tenant_id)

    def get_user_profile(self, context: RequestContext, user_id: str) -> Optional[User]:
        """Get user profile information."""
        return self.user_repo.get_by_id(context, user_id)

    def get_business_data(self, context: RequestContext) -> Optional[BusinessData]:
        """Get shared business data for tenant."""
        return self.business_repo.get_by_tenant(context)

    def update_business_data_from_coaching(self, context: RequestContext, topic: CoachingTopic, outcomes: Dict[str, Any]) -> bool:
        """Update business data based on coaching session outcomes."""
        logger.info("Updating business data from coaching", topic=topic, user_id=context.user_id)

        # Map coaching topics to business data fields
        field_mapping = {
            CoachingTopic.CORE_VALUES: 'core_values',
            CoachingTopic.PURPOSE: 'purpose',
            CoachingTopic.VISION: 'vision',
            CoachingTopic.GOALS: 'goals'
        }

        field = field_mapping.get(topic)
        if not field:
            logger.warning("Unknown coaching topic", topic=topic)
            return False

        # Extract the relevant outcome data
        if field in outcomes:
            return self.business_repo.update_field(
                context,
                field,
                outcomes[field],
                context.user_id
            )

        return False

    def check_subscription_limits(self, context: RequestContext, action: str) -> Dict[str, Any]:
        """Check subscription limits for various actions."""
        # This would integrate with subscription repository
        # For now, return a placeholder
        return {
            'allowed': True,
            'remaining': 100,
            'limit': 100,
            'resets_at': None
        }
