from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CalendarIntegrationResponse(BaseModel):
    id: UUID
    member_id: UUID
    provider: str
    external_calendar_id: str
    sync_enabled: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class GoogleAuthUrlResponse(BaseModel):
    auth_url: str


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


class CalDAVIntegrationCreate(BaseModel):
    calendar_url: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class SyncResult(BaseModel):
    integration_id: str
    provider: str
    created: int
    updated: int
    skipped: int
    error: str | None = None


class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    location: str | None = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    member_id: UUID | None = None


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    all_day: bool | None = None


class CalendarEventResponse(BaseModel):
    id: UUID
    household_id: UUID
    member_id: UUID | None
    external_id: str | None
    source: str | None
    title: str
    description: str | None
    location: str | None
    start_time: datetime
    end_time: datetime
    all_day: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
