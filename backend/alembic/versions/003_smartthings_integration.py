"""add smartthings integration tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create device_type enum
    device_type_enum = postgresql.ENUM(
        "washer", "dryer", "dishwasher", "robot_vacuum",
        "refrigerator", "oven", "air_purifier", "smart_plug", "other",
        name="device_type",
        create_type=True,
    )
    device_type_enum.create(op.get_bind(), checkfirst=True)

    # Create device_event_type enum
    device_event_type_enum = postgresql.ENUM(
        "cycle_started", "cycle_completed", "door_opened", "door_closed",
        "error", "power_on", "power_off", "filter_alert", "temperature_alert",
        name="device_event_type",
        create_type=True,
    )
    device_event_type_enum.create(op.get_bind(), checkfirst=True)

    # Add new values to existing enums
    op.execute("ALTER TYPE vector_source_type ADD VALUE IF NOT EXISTS 'device_event'")
    op.execute("ALTER TYPE pattern_type ADD VALUE IF NOT EXISTS 'appliance_usage'")

    # Create smartthings_integrations table
    op.create_table(
        "smartthings_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("installed_app_id", sa.String(), nullable=True),
        sa.Column("location_id", sa.String(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_st_integrations_household", "smartthings_integrations", ["household_id"])

    # Create smartthings_devices table
    op.create_table(
        "smartthings_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smartthings_integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_device_id", sa.String(), nullable=False),
        sa.Column("device_type", device_type_enum, nullable=False, server_default="other"),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("room", sa.String(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("current_state", postgresql.JSONB(), nullable=True),
        sa.Column("is_running", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cycle_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_cycles", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_st_devices_household", "smartthings_devices", ["household_id"])
    op.create_index("idx_st_devices_external", "smartthings_devices", ["external_device_id"])

    # Create device_events table
    op.create_table(
        "device_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smartthings_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", device_event_type_enum, nullable=False),
        sa.Column("event_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_device_events_device", "device_events", ["device_id"])
    op.create_index("idx_device_events_created", "device_events", ["created_at"])

    # Create device_consumables table
    op.create_table(
        "device_consumables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smartthings_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usage_per_cycle", sa.Numeric(), nullable=False, server_default="1"),
        sa.Column("auto_deduct", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_consumables_device", "device_consumables", ["device_id"])
    op.create_unique_constraint("uq_device_consumable", "device_consumables", ["device_id", "inventory_item_id"])


def downgrade() -> None:
    op.drop_table("device_consumables")
    op.drop_table("device_events")
    op.drop_table("smartthings_devices")
    op.drop_table("smartthings_integrations")

    op.execute("DROP TYPE IF EXISTS device_event_type")
    op.execute("DROP TYPE IF EXISTS device_type")
