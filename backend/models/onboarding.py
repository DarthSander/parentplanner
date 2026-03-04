import uuid
from datetime import date, datetime

from sqlalchemy import String, Integer, Date, Boolean, Text, DateTime, CheckConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, UUIDPrimaryKeyMixin


class OnboardingAnswer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "onboarding_answers"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    child_age_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    situation: Mapped[str] = mapped_column(
        String, nullable=False
    )
    work_situation_owner: Mapped[str] = mapped_column(
        String, nullable=False
    )
    work_situation_partner: Mapped[str | None] = mapped_column(String, nullable=True)
    daycare_days: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    has_caregiver: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pain_points: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    ai_generated_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "situation IN ('couple', 'single', 'co_parent')",
            name="ck_onboarding_situation",
        ),
        CheckConstraint(
            "work_situation_owner IN ('fulltime', 'parttime', 'leave', 'none')",
            name="ck_onboarding_work_owner",
        ),
        CheckConstraint(
            "work_situation_partner IN ('fulltime', 'parttime', 'leave', 'none')",
            name="ck_onboarding_work_partner",
        ),
    )
