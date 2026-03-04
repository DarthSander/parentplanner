import uuid
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Text, ForeignKey, CheckConstraint,
    DateTime, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class CalendarEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calendar_events"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_context_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    household = relationship("Household", back_populates="calendar_events")

    __table_args__ = (
        CheckConstraint(
            "source IN ('google', 'caldav', 'manual')",
            name="ck_calendar_source",
        ),
    )


class CalendarIntegration(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "calendar_integrations"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    external_calendar_id: Mapped[str] = mapped_column(String, nullable=False)
    access_token: Mapped[str | None] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "provider IN ('google', 'caldav')",
            name="ck_calendar_integration_provider",
        ),
    )
