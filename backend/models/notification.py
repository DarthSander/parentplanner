import enum
import uuid
from datetime import datetime, time

from sqlalchemy import (
    String, Integer, Boolean, Numeric, Text, Enum, ForeignKey, Time,
    CheckConstraint, DateTime, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class NotificationChannel(str, enum.Enum):
    push = "push"
    email = "email"
    whatsapp = "whatsapp"


class NotificationStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"
    acted_upon = "acted_upon"
    ignored = "ignored"


class NotificationProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_profiles"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    preferred_channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel"), nullable=False, default=NotificationChannel.push
    )
    aggression_level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    response_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    best_response_window_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    best_response_window_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    partner_escalation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    partner_escalation_after_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    fcm_token: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    member = relationship("Member", back_populates="notification_profile")

    __table_args__ = (
        CheckConstraint(
            "aggression_level BETWEEN 1 AND 5",
            name="ck_notification_aggression",
        ),
    )


class NotificationLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notification_log"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel", create_type=False), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    related_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    related_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"), nullable=False, default=NotificationStatus.sent
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
