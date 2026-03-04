from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemberRole(str, Enum):
    owner = "owner"
    partner = "partner"
    caregiver = "caregiver"
    daycare = "daycare"


class MemberInvite(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.partner
    display_name: str = Field(..., min_length=1, max_length=100)


class MemberUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = None


class MemberResponse(BaseModel):
    id: UUID
    household_id: UUID
    role: MemberRole
    display_name: str
    email: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteAcceptRequest(BaseModel):
    token: str


class InviteValidateResponse(BaseModel):
    valid: bool
    household_name: str | None = None
    role: str | None = None
    display_name: str | None = None
    email: str | None = None
