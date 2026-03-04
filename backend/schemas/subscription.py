from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class SubscriptionTier(str, Enum):
    free = "free"
    standard = "standard"
    family = "family"


class SubscriptionResponse(BaseModel):
    id: UUID
    household_id: UUID
    tier: SubscriptionTier
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_ends_at: datetime | None

    model_config = {"from_attributes": True}
