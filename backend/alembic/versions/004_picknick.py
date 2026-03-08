"""add picknick integration tables

Revision ID: 004
Revises: 003
Create Date: 2026-03-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend vector_source_type enum with picknick source types
    op.execute("ALTER TYPE vector_source_type ADD VALUE IF NOT EXISTS 'picknick_item'")
    op.execute("ALTER TYPE vector_source_type ADD VALUE IF NOT EXISTS 'picknick_order'")

    # Extend pattern_type enum with shopping patterns
    op.execute("ALTER TYPE pattern_type ADD VALUE IF NOT EXISTS 'shopping_frequency'")
    op.execute("ALTER TYPE pattern_type ADD VALUE IF NOT EXISTS 'brand_affinity'")
    op.execute("ALTER TYPE pattern_type ADD VALUE IF NOT EXISTS 'seasonal_shopping'")

    # Create picknick_integrations table
    op.create_table(
        "picknick_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("encrypted_email", sa.Text(), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="NL"),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_picknick_integrations_household", "picknick_integrations", ["household_id"])

    # Create picknick_products (cached catalog) table
    op.create_table(
        "picknick_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("picknick_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("subcategory", sa.String(), nullable=True),
        sa.Column("price", sa.Numeric(), nullable=True),
        sa.Column("unit_quantity", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_picknick_products_household", "picknick_products", ["household_id"])
    op.create_unique_constraint(
        "uq_picknick_product", "picknick_products", ["household_id", "picknick_id"]
    )

    # Create picknick_shopping_lists table
    op.create_table(
        "picknick_shopping_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "integration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("picknick_integrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(), nullable=False, server_default="Boodschappenlijst"),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_picknick_lists_household", "picknick_shopping_lists", ["household_id"])

    # Create picknick_list_items table
    op.create_table(
        "picknick_list_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "list_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("picknick_shopping_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "picknick_product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("picknick_products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "inventory_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("ai_suggested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ai_reason", sa.Text(), nullable=True),
        sa.Column(
            "added_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_picknick_list_items_list", "picknick_list_items", ["list_id"])

    # Create picknick_order_history table
    op.create_table(
        "picknick_order_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "integration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("picknick_integrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("picknick_order_id", sa.String(), nullable=False, unique=True),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_price", sa.Numeric(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("items_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_picknick_orders_household", "picknick_order_history", ["household_id"])


def downgrade() -> None:
    op.drop_table("picknick_order_history")
    op.drop_table("picknick_list_items")
    op.drop_table("picknick_shopping_lists")
    op.drop_table("picknick_products")
    op.drop_table("picknick_integrations")
