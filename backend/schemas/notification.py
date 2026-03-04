from datetime import datetime, time
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationChannelEnum(str, Enum):
    push = "push"
    email = "email"
    whatsapp = "whatsapp"


class NotificationPreferencesUpdate(BaseModel):
    preferred_channel: NotificationChannelEnum | None = None
    aggression_level: int | None = Field(None, ge=1, le=5)
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None
    partner_escalation_enabled: bool | None = None
    partner_escalation_after_days: int | None = Field(None, ge=1, le=14)
    fcm_token: str | None = None


class NotificationPreferencesResponse(BaseModel):
    id: UUID
    member_id: UUID
    preferred_channel: str
    aggression_level: int
    quiet_hours_start: time | None
    quiet_hours_end: time | None
    partner_escalation_enabled: bool
    partner_escalation_after_days: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationLogResponse(BaseModel):
    id: UUID
    channel: str
    title: str
    body: str
    status: str
    sent_at: datetime
    read_at: datetime | None

    model_config = {"from_attributes": True}
