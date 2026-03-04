import uuid
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Text, Numeric, ForeignKey, CheckConstraint,
    DateTime, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class InventoryItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_items"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    current_quantity: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String, nullable=False, default="stuks")
    threshold_quantity: Mapped[float] = mapped_column(Numeric, nullable=False, default=1)
    average_consumption_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    last_restocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferred_store_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    household = relationship("Household", back_populates="inventory_items")
    alerts = relationship("InventoryAlert", back_populates="item", cascade="all, delete-orphan")


class InventoryAlert(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inventory_alerts"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    reported_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    item = relationship("InventoryItem", back_populates="alerts")

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('low_stock', 'out_of_stock', 'caregiver_report')",
            name="ck_inventory_alert_type",
        ),
    )
