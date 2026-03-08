import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Household(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    members = relationship("Member", back_populates="household", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="household", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="household", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="household", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="household", cascade="all, delete-orphan")
    vector_documents = relationship("VectorDocument", back_populates="household", cascade="all, delete-orphan")
    daycare_contacts = relationship("DaycareContact", back_populates="household", cascade="all, delete-orphan")
    smartthings_integrations = relationship("SmartThingsIntegration", back_populates="household", cascade="all, delete-orphan")
    smartthings_devices = relationship("SmartThingsDevice", back_populates="household", cascade="all, delete-orphan")
