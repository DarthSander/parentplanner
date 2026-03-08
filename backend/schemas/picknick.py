from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Connect / Status ──────────────────────────────────────────────────────────

class PicknickConnectRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=1, max_length=200)
    country_code: str = Field("NL", pattern="^(NL|DE|BE)$")


class PicknickStatusResponse(BaseModel):
    connected: bool
    country_code: str | None = None
    last_synced_at: datetime | None = None
    list_count: int = 0
    integration_id: UUID | None = None


# ── Products ─────────────────────────────────────────────────────────────────

class PicknickProductResponse(BaseModel):
    id: UUID
    picknick_id: str
    name: str
    category: str | None
    subcategory: str | None
    price: float | None
    unit_quantity: str | None
    image_url: str | None
    available: bool

    class Config:
        from_attributes = True


# ── Shopping Lists ────────────────────────────────────────────────────────────

class PicknickListItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(1.0, ge=0.01)
    unit: str | None = None
    picknick_product_id: UUID | None = None
    inventory_item_id: UUID | None = None


class PicknickListItemUpdate(BaseModel):
    quantity: float | None = Field(None, ge=0.01)
    checked: bool | None = None
    picknick_product_id: UUID | None = None


class PicknickListItemResponse(BaseModel):
    id: UUID
    name: str
    quantity: float
    unit: str | None
    ai_suggested: bool
    ai_reason: str | None
    checked: bool
    picknick_product_id: UUID | None
    inventory_item_id: UUID | None
    picknick_product: PicknickProductResponse | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PicknickShoppingListCreate(BaseModel):
    name: str = Field("Boodschappenlijst", min_length=1, max_length=200)
    notes: str | None = None


class PicknickShoppingListResponse(BaseModel):
    id: UUID
    household_id: UUID
    name: str
    status: str
    ai_generated: bool
    notes: str | None
    item_count: int = 0
    sent_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PicknickShoppingListDetailResponse(PicknickShoppingListResponse):
    items: list[PicknickListItemResponse] = []


# ── Recommendations ───────────────────────────────────────────────────────────

class PicknickRecommendedItem(BaseModel):
    name: str
    quantity: float
    unit: str | None
    reason: str
    priority: str  # "urgent" | "normal" | "suggestion"
    source: str    # "inventory_low" | "pattern" | "calendar" | "smartthings"
    picknick_product_id: UUID | None = None
    inventory_item_id: UUID | None = None
    estimated_price: float | None = None


class PicknickRecommendationsResponse(BaseModel):
    items: list[PicknickRecommendedItem]
    generated_at: datetime
    context_summary: str


# ── Send to Picknick ──────────────────────────────────────────────────────────

class SendToPicknickResponse(BaseModel):
    success: bool
    items_sent: int
    items_failed: int
    message: str


# ── Order History ────────────────────────────────────────────────────────────

class PicknickOrderResponse(BaseModel):
    id: UUID
    picknick_order_id: str
    order_date: datetime | None
    delivery_date: datetime | None
    total_price: float | None
    status: str | None
    item_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
