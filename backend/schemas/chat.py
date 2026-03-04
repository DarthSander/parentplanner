from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    id: UUID
    household_id: UUID
    member_id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    reply: str
    message_id: UUID
    created_at: datetime
