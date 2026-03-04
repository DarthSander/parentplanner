import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class MemberRole(str, enum.Enum):
    owner = "owner"
    partner = "partner"
    caregiver = "caregiver"
    daycare = "daycare"


class Member(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "members"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole, name="member_role"), nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    household = relationship("Household", back_populates="members")
    notification_profile = relationship("NotificationProfile", back_populates="member", uselist=False)
