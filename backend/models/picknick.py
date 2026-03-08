import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PicknickListStatus(str, enum.Enum):
    open = "open"
    sent_to_picknick = "sent_to_picknick"
    delivered = "delivered"


class PicknickIntegration(UUIDPrimaryKeyMixin, Base):
    """Stores encrypted Picknick credentials per household."""

    __tablename__ = "picknick_integrations"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False
    )
    # Credentials stored encrypted via Fernet
    encrypted_email: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="NL")
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    household = relationship("Household", back_populates="picknick_integration")
    shopping_lists = relationship("PicknickShoppingList", back_populates="integration", cascade="all, delete-orphan")


class PicknickProduct(UUIDPrimaryKeyMixin, Base):
    """Cached Picknick product catalog per household (from search results)."""

    __tablename__ = "picknick_products"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    picknick_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    unit_quantity: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "1 liter", "6 stuks"
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("household_id", "picknick_id", name="uq_picknick_product"),
    )


class PicknickShoppingList(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A shopping list in GezinsAI that can be pushed to Picknick."""

    __tablename__ = "picknick_shopping_lists"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("picknick_integrations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False, default="Boodschappenlijst")
    status: Mapped[PicknickListStatus] = mapped_column(
        String, nullable=False, default=PicknickListStatus.open
    )
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    integration = relationship("PicknickIntegration", back_populates="shopping_lists")
    items = relationship("PicknickListItem", back_populates="shopping_list", cascade="all, delete-orphan")


class PicknickListItem(UUIDPrimaryKeyMixin, Base):
    """A single item in a GezinsAI shopping list."""

    __tablename__ = "picknick_list_items"

    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("picknick_shopping_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    picknick_product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("picknick_products.id", ondelete="SET NULL"), nullable=True
    )
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)  # fallback when no product match
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False, default=1)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    shopping_list = relationship("PicknickShoppingList", back_populates="items")
    picknick_product = relationship("PicknickProduct")
    inventory_item = relationship("InventoryItem")


class PicknickOrderHistory(UUIDPrimaryKeyMixin, Base):
    """Cached Picknick order history for pattern analysis."""

    __tablename__ = "picknick_order_history"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("picknick_integrations.id", ondelete="CASCADE"), nullable=False
    )
    picknick_order_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    items_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # full order items snapshot
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
