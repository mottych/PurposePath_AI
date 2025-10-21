"""Enhanced repository base classes using Pydantic models for type safety.

This module provides base repository classes that replace dict[str, Any] usage
with proper Pydantic models, following domain-driven design principles.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from shared.models.domain import KPI, Goal, Issue
from shared.models.multitenant import User
from shared.types.common import JSONDict

# Generic type for domain models
T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """Base repository class with Pydantic model support."""

    def __init__(self, table: Any, model_class: type[T]) -> None:
        self.table = table
        self.model_class = model_class

    def _item_to_model(self, item: JSONDict) -> T:
        """Convert DynamoDB item to Pydantic model."""
        try:
            # Remove DynamoDB-specific fields that aren't part of the domain model
            clean_item = {
                k: v
                for k, v in item.items()
                if not k.startswith("_") and k not in ["GSI1PK", "GSI1SK"]
            }
            return self.model_class.model_validate(clean_item)
        except Exception as e:
            raise ValueError(f"Failed to convert item to {self.model_class.__name__}: {e}") from e

    def _model_to_item(self, model: T, tenant_id: str) -> JSONDict:
        """Convert Pydantic model to DynamoDB item."""
        try:
            # Convert model to dict and add required DynamoDB fields
            item = model.model_dump(exclude_none=True)
            item.update({"tenant_id": tenant_id, "updated_at": datetime.now(UTC).isoformat()})
            return item
        except Exception as e:
            raise ValueError(f"Failed to convert {self.model_class.__name__} to item: {e}") from e

    @abstractmethod
    def create(self, tenant_id: str, model: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def get(self, tenant_id: str, entity_id: str) -> T | None:
        """Get entity by ID."""
        pass

    @abstractmethod
    def update(self, tenant_id: str, entity_id: str, model: T) -> T | None:
        """Update entity."""
        pass

    @abstractmethod
    def delete(self, tenant_id: str, entity_id: str) -> bool:
        """Delete entity."""
        pass

    @abstractmethod
    def list(self, tenant_id: str, limit: int = 20, last_key: str | None = None) -> list[T]:
        """List entities with pagination."""
        pass


class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue domain objects."""

    def __init__(self, table: Any) -> None:
        super().__init__(table, Issue)

    def create(self, tenant_id: str, model: Issue) -> Issue:
        """Create a new issue."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"ISSUE#{model.id}"
        item["created_at"] = datetime.now(UTC).isoformat()

        self.table.put_item(Item=item)
        return self._item_to_model(item)

    def get(self, tenant_id: str, entity_id: str) -> Issue | None:
        """Get issue by ID."""
        try:
            response = self.table.get_item(
                Key={"pk": f"TENANT#{tenant_id}", "sk": f"ISSUE#{entity_id}"}
            )
            if "Item" in response:
                return self._item_to_model(response["Item"])
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get issue {entity_id}: {e}") from e

    def update(self, tenant_id: str, entity_id: str, model: Issue) -> Issue | None:
        """Update issue."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"ISSUE#{entity_id}"

        try:
            self.table.put_item(Item=item, ReturnValues="ALL_OLD")
            return self._item_to_model(item)
        except Exception as e:
            raise RuntimeError(f"Failed to update issue {entity_id}: {e}") from e

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        """Delete issue."""
        try:
            self.table.delete_item(Key={"pk": f"TENANT#{tenant_id}", "sk": f"ISSUE#{entity_id}"})
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete issue {entity_id}: {e}") from e

    def list(self, tenant_id: str, limit: int = 20, last_key: str | None = None) -> list[Issue]:
        """List issues with pagination."""
        try:
            query_kwargs: dict[str, Any] = {
                "KeyConditionExpression": "pk = :pk AND begins_with(sk, :sk_prefix)",
                "ExpressionAttributeValues": {":pk": f"TENANT#{tenant_id}", ":sk_prefix": "ISSUE#"},
                "Limit": limit,
            }

            if last_key:
                query_kwargs["ExclusiveStartKey"] = {"pk": f"TENANT#{tenant_id}", "sk": last_key}

            response = self.table.query(**query_kwargs)
            return [self._item_to_model(item) for item in response.get("Items", [])]
        except Exception as e:
            raise RuntimeError(f"Failed to list issues: {e}") from e


class GoalRepository(BaseRepository[Goal]):
    """Repository for Goal domain objects."""

    def __init__(self, table: Any) -> None:
        super().__init__(table, Goal)

    def create(self, tenant_id: str, model: Goal) -> Goal:
        """Create a new goal."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"GOAL#{model.id}"
        item["created_at"] = datetime.now(UTC).isoformat()

        self.table.put_item(Item=item)
        return self._item_to_model(item)

    def get(self, tenant_id: str, entity_id: str) -> Goal | None:
        """Get goal by ID."""
        try:
            response = self.table.get_item(
                Key={"pk": f"TENANT#{tenant_id}", "sk": f"GOAL#{entity_id}"}
            )
            if "Item" in response:
                return self._item_to_model(response["Item"])
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get goal {entity_id}: {e}") from e

    def update(self, tenant_id: str, entity_id: str, model: Goal) -> Goal | None:
        """Update goal."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"GOAL#{entity_id}"

        try:
            self.table.put_item(Item=item)
            return self._item_to_model(item)
        except Exception as e:
            raise RuntimeError(f"Failed to update goal {entity_id}: {e}") from e

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        """Delete goal."""
        try:
            self.table.delete_item(Key={"pk": f"TENANT#{tenant_id}", "sk": f"GOAL#{entity_id}"})
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete goal {entity_id}: {e}") from e

    def list(self, tenant_id: str, limit: int = 20, last_key: str | None = None) -> list[Goal]:
        """List goals with pagination."""
        try:
            query_kwargs: dict[str, Any] = {
                "KeyConditionExpression": "pk = :pk AND begins_with(sk, :sk_prefix)",
                "ExpressionAttributeValues": {":pk": f"TENANT#{tenant_id}", ":sk_prefix": "GOAL#"},
                "Limit": limit,
            }

            if last_key:
                query_kwargs["ExclusiveStartKey"] = {"pk": f"TENANT#{tenant_id}", "sk": last_key}

            response = self.table.query(**query_kwargs)
            return [self._item_to_model(item) for item in response.get("Items", [])]
        except Exception as e:
            raise RuntimeError(f"Failed to list goals: {e}") from e


class KPIRepository(BaseRepository[KPI]):
    """Repository for KPI domain objects."""

    def __init__(self, table: Any) -> None:
        super().__init__(table, KPI)

    def create(self, tenant_id: str, model: KPI) -> KPI:
        """Create a new KPI."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"KPI#{model.id}"
        item["created_at"] = datetime.now(UTC).isoformat()

        self.table.put_item(Item=item)
        return self._item_to_model(item)

    def get(self, tenant_id: str, entity_id: str) -> KPI | None:
        """Get KPI by ID."""
        try:
            response = self.table.get_item(
                Key={"pk": f"TENANT#{tenant_id}", "sk": f"KPI#{entity_id}"}
            )
            if "Item" in response:
                return self._item_to_model(response["Item"])
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get KPI {entity_id}: {e}") from e

    def update(self, tenant_id: str, entity_id: str, model: KPI) -> KPI | None:
        """Update KPI."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"KPI#{entity_id}"

        try:
            self.table.put_item(Item=item)
            return self._item_to_model(item)
        except Exception as e:
            raise RuntimeError(f"Failed to update KPI {entity_id}: {e}") from e

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        """Delete KPI."""
        try:
            self.table.delete_item(Key={"pk": f"TENANT#{tenant_id}", "sk": f"KPI#{entity_id}"})
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete KPI {entity_id}: {e}") from e

    def list(self, tenant_id: str, limit: int = 20, last_key: str | None = None) -> list[KPI]:
        """List KPIs with pagination."""
        try:
            query_kwargs: dict[str, Any] = {
                "KeyConditionExpression": "pk = :pk AND begins_with(sk, :sk_prefix)",
                "ExpressionAttributeValues": {":pk": f"TENANT#{tenant_id}", ":sk_prefix": "KPI#"},
                "Limit": limit,
            }

            if last_key:
                query_kwargs["ExclusiveStartKey"] = {"pk": f"TENANT#{tenant_id}", "sk": last_key}

            response = self.table.query(**query_kwargs)
            return [self._item_to_model(item) for item in response.get("Items", [])]
        except Exception as e:
            raise RuntimeError(f"Failed to list KPIs: {e}") from e


class UserRepository(BaseRepository[User]):
    """Repository for User domain objects."""

    def __init__(self, table: Any) -> None:
        super().__init__(table, User)

    def create(self, tenant_id: str, model: User) -> User:
        """Create a new user."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"USER#{model.user_id}"
        item["created_at"] = datetime.now(UTC).isoformat()

        self.table.put_item(Item=item)
        return self._item_to_model(item)

    def get(self, tenant_id: str, entity_id: str) -> User | None:
        """Get user by ID."""
        try:
            response = self.table.get_item(
                Key={"pk": f"TENANT#{tenant_id}", "sk": f"USER#{entity_id}"}
            )
            if "Item" in response:
                return self._item_to_model(response["Item"])
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get user {entity_id}: {e}") from e

    def get_by_email(self, tenant_id: str, email: str) -> User | None:
        """Get user by email address."""
        try:
            # This would typically use a GSI for email lookups
            response = self.table.query(
                IndexName="email-index",  # Assume email GSI exists
                KeyConditionExpression="email = :email",
                ExpressionAttributeValues={":email": email},
            )
            items = response.get("Items", [])
            if items:
                # Filter by tenant for security
                tenant_items = [item for item in items if item.get("tenant_id") == tenant_id]
                if tenant_items:
                    return self._item_to_model(tenant_items[0])
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get user by email {email}: {e}") from e

    def update(self, tenant_id: str, entity_id: str, model: User) -> User | None:
        """Update user."""
        item = self._model_to_item(model, tenant_id)
        item["pk"] = f"TENANT#{tenant_id}"
        item["sk"] = f"USER#{entity_id}"

        try:
            self.table.put_item(Item=item)
            return self._item_to_model(item)
        except Exception as e:
            raise RuntimeError(f"Failed to update user {entity_id}: {e}") from e

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        """Delete user."""
        try:
            self.table.delete_item(Key={"pk": f"TENANT#{tenant_id}", "sk": f"USER#{entity_id}"})
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete user {entity_id}: {e}") from e

    def list(self, tenant_id: str, limit: int = 20, last_key: str | None = None) -> list[User]:
        """List users with pagination."""
        try:
            query_kwargs: dict[str, Any] = {
                "KeyConditionExpression": "pk = :pk AND begins_with(sk, :sk_prefix)",
                "ExpressionAttributeValues": {":pk": f"TENANT#{tenant_id}", ":sk_prefix": "USER#"},
                "Limit": limit,
            }

            if last_key:
                query_kwargs["ExclusiveStartKey"] = {"pk": f"TENANT#{tenant_id}", "sk": last_key}

            response = self.table.query(**query_kwargs)
            return [self._item_to_model(item) for item in response.get("Items", [])]
        except Exception as e:
            raise RuntimeError(f"Failed to list users: {e}") from e
