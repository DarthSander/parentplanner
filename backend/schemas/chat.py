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


class ChatAction(BaseModel):
    action: str  # create_task | add_to_shopping | complete_task | snooze_task
    label: str  # Button text: "Luiers toevoegen aan boodschappen"
    data: dict = {}  # Payload for the action


class ChatResponse(BaseModel):
    reply: str
    actions: list[ChatAction] = []
    message_id: UUID
    created_at: datetime
