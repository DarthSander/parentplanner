import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Numeric, Text, Enum, ForeignKey, CheckConstraint,
    DateTime, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin


class PatternType(str, enum.Enum):
    task_avoidance = "task_avoidance"
    task_affinity = "task_affinity"
    inventory_rate = "inventory_rate"
    schedule_conflict = "schedule_conflict"
    complementary_split = "complementary_split"


class Pattern(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "patterns"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pattern_type: Mapped[PatternType] = mapped_column(
        Enum(PatternType, name="pattern_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric, nullable=False)
    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    acted_upon: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    household = relationship("Household", back_populates="patterns")

    __table_args__ = (
        CheckConstraint(
            "confidence_score BETWEEN 0 AND 1",
            name="ck_pattern_confidence",
        ),
    )
