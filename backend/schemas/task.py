from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    baby_care = "baby_care"
    household = "household"
    work = "work"
    private = "private"


class TaskType(str, Enum):
    quick = "quick"
    prep = "prep"


class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    snoozed = "snoozed"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category: TaskCategory
    task_type: TaskType = TaskType.quick
    assigned_to: UUID | None = None
    due_date: datetime | None = None
    recurrence_rule: str | None = None
    estimated_minutes: int | None = Field(None, ge=1, le=1440)
    dependencies: list[UUID] | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category: TaskCategory | None = None
    task_type: TaskType | None = None
    assigned_to: UUID | None = None
    due_date: datetime | None = None
    recurrence_rule: str | None = None
    estimated_minutes: int | None = Field(None, ge=1, le=1440)
    status: TaskStatus | None = None
    version: int  # required for optimistic locking


class TaskResponse(BaseModel):
    id: UUID
    household_id: UUID
    title: str
    description: str | None
    category: TaskCategory
    task_type: TaskType
    assigned_to: UUID | None
    due_date: datetime | None
    recurrence_rule: str | None
    estimated_minutes: int | None
    dependencies: list[UUID] | None
    status: TaskStatus
    snooze_count: int
    ai_generated: bool
    version: int
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCompleteRequest(BaseModel):
    duration_minutes: int | None = Field(None, ge=1, le=1440)


class TaskDistributionItem(BaseModel):
    member_id: UUID
    display_name: str
    total_completed: int
    total_open: int
    categories: dict[str, int]
