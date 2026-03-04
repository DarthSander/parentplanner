from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str | None = None
    current_quantity: float = Field(0, ge=0)
    unit: str = "stuks"
    threshold_quantity: float = Field(1, ge=0)
    preferred_store_url: str | None = None


class InventoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = None
    current_quantity: float | None = Field(None, ge=0)
    unit: str | None = None
    threshold_quantity: float | None = Field(None, ge=0)
    preferred_store_url: str | None = None


class InventoryResponse(BaseModel):
    id: UUID
    household_id: UUID
    name: str
    category: str | None
    current_quantity: float
    unit: str
    threshold_quantity: float
    average_consumption_rate: float | None
    last_restocked_at: datetime | None
    preferred_store_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LowStockReport(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
