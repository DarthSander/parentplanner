from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HouseholdCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class HouseholdUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)


class HouseholdResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
