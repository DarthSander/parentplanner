"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- Enum types ---
    member_role = postgresql.ENUM(
        "owner", "partner", "caregiver", "daycare", name="member_role", create_type=False
    )
    task_category = postgresql.ENUM(
        "baby_care", "household", "work", "private", name="task_category", create_type=False
    )
    task_type = postgresql.ENUM("quick", "prep", name="task_type", create_type=False)
    task_status = postgresql.ENUM(
        "open", "in_progress", "done", "snoozed", name="task_status", create_type=False
    )
    pattern_type = postgresql.ENUM(
        "task_avoidance", "task_affinity", "inventory_rate",
        "schedule_conflict", "complementary_split",
        name="pattern_type", create_type=False,
    )
    notification_channel = postgresql.ENUM(
        "push", "email", "whatsapp", name="notification_channel", create_type=False
    )
    notification_status = postgresql.ENUM(
        "sent", "delivered", "read", "acted_upon", "ignored",
        name="notification_status", create_type=False,
    )
    vector_source_type = postgresql.ENUM(
        "task", "task_completion", "inventory", "calendar_event",
        "chat_message", "pattern", "onboarding_answer", "summary",
        name="vector_source_type", create_type=False,
    )
    subscription_tier = postgresql.ENUM(
        "free", "standard", "family", name="subscription_tier", create_type=False
    )
    subscription_status = postgresql.ENUM(
        "active", "cancelled", "past_due", "trialing",
        name="subscription_status", create_type=False,
    )

    # Create all enum types
    for enum in [
        member_role, task_category, task_type, task_status, pattern_type,
        notification_channel, notification_status, vector_source_type,
        subscription_tier, subscription_status,
    ]:
        enum.create(op.get_bind(), checkfirst=True)

    # --- households ---
    op.create_table(
        "households",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- members ---
    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", member_role, nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_members_household", "members", ["household_id"])
    op.create_index("idx_members_user", "members", ["user_id"])

    # --- onboarding_answers ---
    op.create_table(
        "onboarding_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("child_age_weeks", sa.Integer(), nullable=True),
        sa.Column("expected_due_date", sa.Date(), nullable=True),
        sa.Column("situation", sa.Text(), nullable=False),
        sa.Column("work_situation_owner", sa.Text(), nullable=False),
        sa.Column("work_situation_partner", sa.Text(), nullable=True),
        sa.Column("daycare_days", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("has_caregiver", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("pain_points", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("ai_generated_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("situation IN ('couple', 'single', 'co_parent')", name="ck_onboarding_situation"),
        sa.CheckConstraint("work_situation_owner IN ('fulltime', 'parttime', 'leave', 'none')", name="ck_onboarding_work_owner"),
        sa.CheckConstraint("work_situation_partner IN ('fulltime', 'parttime', 'leave', 'none')", name="ck_onboarding_work_partner"),
    )

    # --- tasks ---
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", task_category, nullable=False),
        sa.Column("task_type", task_type, nullable=False, server_default="quick"),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_rule", sa.Text(), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("dependencies", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("status", task_status, nullable=False, server_default="open"),
        sa.Column("snooze_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_tasks_household", "tasks", ["household_id"])
    op.create_index("idx_tasks_assigned", "tasks", ["assigned_to"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_due", "tasks", ["due_date"])

    # --- task_completions ---
    op.create_table(
        "task_completions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.create_index("idx_completions_task", "task_completions", ["task_id"])
    op.create_index("idx_completions_member", "task_completions", ["completed_by"])
    op.create_index("idx_completions_household", "task_completions", ["household_id"])

    # --- calendar_events ---
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ai_context_processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source IN ('google', 'caldav', 'manual')", name="ck_calendar_source"),
    )
    op.create_index("idx_calendar_household", "calendar_events", ["household_id"])
    op.create_index("idx_calendar_start", "calendar_events", ["start_time"])
    op.create_index("idx_calendar_member", "calendar_events", ["member_id"])

    # --- inventory_items ---
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("current_quantity", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("unit", sa.Text(), nullable=False, server_default="stuks"),
        sa.Column("threshold_quantity", sa.Numeric(), nullable=False, server_default="1"),
        sa.Column("average_consumption_rate", sa.Numeric(), nullable=True),
        sa.Column("last_restocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferred_store_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_inventory_household", "inventory_items", ["household_id"])

    # --- inventory_alerts ---
    op.create_table(
        "inventory_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reported_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("alert_type IN ('low_stock', 'out_of_stock', 'caregiver_report')", name="ck_inventory_alert_type"),
    )

    # --- patterns ---
    op.create_table(
        "patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pattern_type", pattern_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(), nullable=False),
        sa.Column("first_detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acted_upon", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="ck_pattern_confidence"),
    )
    op.create_index("idx_patterns_household", "patterns", ["household_id"])
    op.create_index("idx_patterns_member", "patterns", ["member_id"])

    # --- notification_profiles ---
    op.create_table(
        "notification_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("preferred_channel", notification_channel, nullable=False, server_default="push"),
        sa.Column("aggression_level", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.Column("response_rate", sa.Numeric(), nullable=True),
        sa.Column("best_response_window_start", sa.Time(), nullable=True),
        sa.Column("best_response_window_end", sa.Time(), nullable=True),
        sa.Column("partner_escalation_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("partner_escalation_after_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("aggression_level BETWEEN 1 AND 5", name="ck_notification_aggression"),
    )

    # --- notification_log ---
    op.create_table(
        "notification_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", notification_status, nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_notifications_member", "notification_log", ["member_id"])

    # --- chat_messages ---
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_role"),
    )
    op.create_index("idx_chat_household", "chat_messages", ["household_id"])
    op.create_index("idx_chat_member", "chat_messages", ["member_id"])
    op.create_index("idx_chat_created", "chat_messages", [sa.text("created_at DESC")])

    # --- vector_documents ---
    op.create_table(
        "vector_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_type", vector_source_type, nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),  # vector(1536) — created via raw SQL below
        sa.Column("embedding_model", sa.Text(), nullable=False, server_default="text-embedding-3-small"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("is_summary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("summarizes_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_vectors_household", "vector_documents", ["household_id"])
    op.create_index("idx_vectors_source", "vector_documents", ["source_type", "source_id"])

    # Replace the text column with actual vector type and create HNSW index
    op.execute("ALTER TABLE vector_documents ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")
    op.execute("""
        CREATE INDEX idx_vectors_embedding ON vector_documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("stripe_subscription_id", sa.Text(), nullable=True, unique=True),
        sa.Column("stripe_customer_id", sa.Text(), nullable=True),
        sa.Column("tier", subscription_tier, nullable=False, server_default="free"),
        sa.Column("status", subscription_status, nullable=False, server_default="trialing"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- calendar_integrations ---
    op.create_table(
        "calendar_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("external_calendar_id", sa.Text(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("provider IN ('google', 'caldav')", name="ck_calendar_integration_provider"),
    )
    op.create_index("idx_calendar_integrations_member", "calendar_integrations", ["member_id"])

    # --- daycare_contacts ---
    op.create_table(
        "daycare_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("briefing_channel", sa.Text(), nullable=False),
        sa.Column("briefing_days", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("briefing_time", sa.Time(), nullable=False, server_default=sa.text("'07:00'")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("briefing_channel IN ('email', 'whatsapp')", name="ck_daycare_channel"),
    )

    # --- sync_queue ---
    op.create_table(
        "sync_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("conflict", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("operation IN ('create', 'update', 'delete')", name="ck_sync_operation"),
    )
    op.create_index("idx_sync_queue_processed", "sync_queue", ["processed", "created_at"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("sync_queue")
    op.drop_table("daycare_contacts")
    op.drop_table("calendar_integrations")
    op.drop_table("subscriptions")
    op.drop_table("vector_documents")
    op.drop_table("chat_messages")
    op.drop_table("notification_log")
    op.drop_table("notification_profiles")
    op.drop_table("patterns")
    op.drop_table("inventory_alerts")
    op.drop_table("inventory_items")
    op.drop_table("calendar_events")
    op.drop_table("task_completions")
    op.drop_table("tasks")
    op.drop_table("onboarding_answers")
    op.drop_table("members")
    op.drop_table("households")

    # Drop enum types
    for enum_name in [
        "subscription_status", "subscription_tier", "vector_source_type",
        "notification_status", "notification_channel", "pattern_type",
        "task_status", "task_type", "task_category", "member_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
