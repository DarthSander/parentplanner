from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SmartThingsAuthURL(BaseModel):
    auth_url: str


class SmartThingsCallback(BaseModel):
    code: str
    state: str | None = None


class SmartThingsStatusResponse(BaseModel):
    connected: bool
    location_id: str | None = None
    last_synced_at: datetime | None = None
    device_count: int = 0


class DeviceResponse(BaseModel):
    id: UUID
    household_id: UUID
    external_device_id: str
    device_type: str
    label: str
    room: str | None
    capabilities: dict | None
    current_state: dict | None
    is_running: bool
    cycle_started_at: datetime | None
    last_event_at: datetime | None
    total_cycles: int
    sync_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=200)
    room: str | None = None
    sync_enabled: bool | None = None


class ConsumableCreate(BaseModel):
    inventory_item_id: UUID
    usage_per_cycle: float = Field(1, gt=0)
    auto_deduct: bool = True


class ConsumableUpdate(BaseModel):
    usage_per_cycle: float | None = Field(None, gt=0)
    auto_deduct: bool | None = None


class ConsumableResponse(BaseModel):
    id: UUID
    device_id: UUID
    inventory_item_id: UUID
    inventory_item_name: str | None = None
    usage_per_cycle: float
    auto_deduct: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceEventResponse(BaseModel):
    id: UUID
    device_id: UUID
    event_type: str
    event_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceStatsResponse(BaseModel):
    total_cycles: int
    cycles_this_week: int
    cycles_this_month: int
    avg_cycles_per_week: float
    consumables_status: list[dict]
