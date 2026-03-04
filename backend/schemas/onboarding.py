from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Situation(str, Enum):
    couple = "couple"
    single = "single"
    co_parent = "co_parent"


class WorkSituation(str, Enum):
    fulltime = "fulltime"
    parttime = "parttime"
    leave = "leave"
    none = "none"


class PainPoint(str, Enum):
    sleep_deprivation = "sleep_deprivation"
    task_distribution = "task_distribution"
    groceries = "groceries"
    schedule = "schedule"
    finances = "finances"


class OnboardingCreate(BaseModel):
    child_name: str | None = Field(None, max_length=100)
    child_age_weeks: int | None = Field(None, ge=0, le=260)
    expected_due_date: date | None = None
    situation: Situation
    work_situation_owner: WorkSituation
    work_situation_partner: WorkSituation | None = None
    daycare_days: list[str] | None = None
    has_caregiver: bool = False
    caregiver_name: str | None = None
    caregiver_role: str | None = None
    pain_points: list[PainPoint] | None = None


class OnboardingResponse(BaseModel):
    id: UUID
    household_id: UUID
    child_age_weeks: int | None
    expected_due_date: date | None
    situation: str
    work_situation_owner: str
    work_situation_partner: str | None
    daycare_days: list[str] | None
    has_caregiver: bool
    pain_points: list[str] | None
    ai_generated_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
