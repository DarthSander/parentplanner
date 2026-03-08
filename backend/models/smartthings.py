import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

from sqlalchemy import DateTime, func


class DeviceType(str, enum.Enum):
    washer = "washer"
    dryer = "dryer"
    dishwasher = "dishwasher"
    robot_vacuum = "robot_vacuum"
    refrigerator = "refrigerator"
    oven = "oven"
    air_purifier = "air_purifier"
    smart_plug = "smart_plug"
    other = "other"


class DeviceEventType(str, enum.Enum):
    cycle_started = "cycle_started"
    cycle_completed = "cycle_completed"
    door_opened = "door_opened"
    door_closed = "door_closed"
    error = "error"
    power_on = "power_on"
    power_off = "power_off"
    filter_alert = "filter_alert"
    temperature_alert = "temperature_alert"


class SmartThingsIntegration(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "smartthings_integrations"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    installed_app_id: Mapped[str | None] = mapped_column(String, nullable=True)
    location_id: Mapped[str | None] = mapped_column(String, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    household = relationship("Household", back_populates="smartthings_integrations")
    devices = relationship("SmartThingsDevice", back_populates="integration", cascade="all, delete-orphan")


class SmartThingsDevice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "smartthings_devices"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smartthings_integrations.id", ondelete="CASCADE"), nullable=False
    )
    external_device_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, name="device_type"), nullable=False, default=DeviceType.other
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    room: Mapped[str | None] = mapped_column(String, nullable=True)
    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    current_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_running: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cycle_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_cycles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    household = relationship("Household", back_populates="smartthings_devices")
    integration = relationship("SmartThingsIntegration", back_populates="devices")
    events = relationship("DeviceEvent", back_populates="device", cascade="all, delete-orphan")
    consumables = relationship("DeviceConsumable", back_populates="device", cascade="all, delete-orphan")


class DeviceEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "device_events"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smartthings_devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[DeviceEventType] = mapped_column(
        Enum(DeviceEventType, name="device_event_type"), nullable=False
    )
    event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    device = relationship("SmartThingsDevice", back_populates="events")


class DeviceConsumable(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "device_consumables"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smartthings_devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False
    )
    usage_per_cycle: Mapped[float] = mapped_column(Numeric, nullable=False, default=1)
    auto_deduct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    device = relationship("SmartThingsDevice", back_populates="consumables")
    inventory_item = relationship("InventoryItem")

    __table_args__ = (
        UniqueConstraint("device_id", "inventory_item_id", name="uq_device_consumable"),
    )
