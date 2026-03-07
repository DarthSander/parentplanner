"""add event_type to calendar_events and linked_calendar_event_id to tasks

Revision ID: 002
Revises: 001
Create Date: 2026-03-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add event_type column to calendar_events for AI classification caching
    op.add_column(
        "calendar_events",
        sa.Column("event_type", sa.String(), nullable=True),
    )

    # Add linked_calendar_event_id to tasks for write-back on completion
    op.add_column(
        "tasks",
        sa.Column(
            "linked_calendar_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calendar_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Widen the calendar_source check constraint to also allow 'outlook'
    op.drop_constraint("ck_calendar_source", "calendar_events", type_="check")
    op.create_check_constraint(
        "ck_calendar_source",
        "calendar_events",
        "source IN ('google', 'caldav', 'manual', 'outlook')",
    )

    # Widen the calendar_integration_provider constraint to also allow 'outlook'
    op.drop_constraint("ck_calendar_integration_provider", "calendar_integrations", type_="check")
    op.create_check_constraint(
        "ck_calendar_integration_provider",
        "calendar_integrations",
        "provider IN ('google', 'caldav', 'outlook')",
    )


def downgrade() -> None:
    op.drop_column("tasks", "linked_calendar_event_id")
    op.drop_column("calendar_events", "event_type")

    op.drop_constraint("ck_calendar_source", "calendar_events", type_="check")
    op.create_check_constraint(
        "ck_calendar_source",
        "calendar_events",
        "source IN ('google', 'caldav', 'manual')",
    )

    op.drop_constraint("ck_calendar_integration_provider", "calendar_integrations", type_="check")
    op.create_check_constraint(
        "ck_calendar_integration_provider",
        "calendar_integrations",
        "provider IN ('google', 'caldav')",
    )
