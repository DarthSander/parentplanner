import uuid
from datetime import datetime, time

from sqlalchemy import String, Boolean, Time, ForeignKey, CheckConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin


class DaycareContact(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "daycare_contacts"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    briefing_channel: Mapped[str] = mapped_column(String, nullable=False)
    briefing_days: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    briefing_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(7, 0))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    household = relationship("Household", back_populates="daycare_contacts")

    __table_args__ = (
        CheckConstraint(
            "briefing_channel IN ('email', 'whatsapp')",
            name="ck_daycare_channel",
        ),
    )
