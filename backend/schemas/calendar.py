from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
