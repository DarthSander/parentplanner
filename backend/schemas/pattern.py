from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PatternResponse(BaseModel):
    id: UUID
    household_id: UUID
    member_id: UUID | None
    pattern_type: str
    description: str
    confidence_score: float
    first_detected_at: datetime
    last_confirmed_at: datetime
    acted_upon: bool

    model_config = {"from_attributes": True}
