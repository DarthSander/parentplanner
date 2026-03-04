from pydantic import BaseModel, Field


class AIGeneratedTask(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str = "baby_care"
    task_type: str = "prep"
    estimated_minutes: int | None = Field(None, ge=1, le=1440)
    due_date: str  # ISO datetime string


class AIGeneratedPattern(BaseModel):
    pattern_type: str
    member_id: str | None = None
    description: str
    confidence_score: float = Field(..., ge=0, le=1)
    metadata: dict | None = None
