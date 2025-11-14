from datetime import datetime

from pydantic import BaseModel, Field


class AvailableTopic(BaseModel):
    topic_id: str = Field(..., description="Topic identifier", alias="id")
    topic_name: str = Field(..., description="Human-readable topic name", alias="name")
    category: str = Field(..., description="Topic category")
    description: str | None = Field(None, description="Topic description")
    display_order: int = Field(..., description="Ordering for UI", alias="displayOrder")
    created_at: datetime | None = Field(None, description="Creation time", alias="createdAt")
    updated_at: datetime | None = Field(None, description="Last update time", alias="updatedAt")

    model_config = {"populate_by_name": True}


__all__ = ["AvailableTopic"]
