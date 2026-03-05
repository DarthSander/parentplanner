"""GDPR account endpoints: data export and account deletion."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.security import get_current_user_id
from models.calendar import CalendarEvent, CalendarIntegration
from models.chat import ChatMessage
from models.daycare import DaycareContact
from models.household import Household
from models.inventory import InventoryAlert, InventoryItem
from models.member import Member
from models.notification import NotificationLog, NotificationProfile
from models.onboarding import OnboardingAnswer
from models.pattern import Pattern
from models.subscription import Subscription
from models.sync import SyncQueueItem
from models.task import Task, TaskCompletion
from models.vector import VectorDocument

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize_row(obj, exclude_fields: set | None = None) -> dict:
    """Serialize a SQLAlchemy model instance to a dict."""
    exclude = exclude_fields or set()
    data = {}
    for col in obj.__table__.columns:
        if col.name in exclude:
            continue
        val = getattr(obj, col.name)
        if isinstance(val, UUID):
            val = str(val)
        elif isinstance(val, datetime):
            val = val.isoformat()
        elif hasattr(val, "value"):  # Enum
            val = val.value
        data[col.name] = val
    return data


async def _export_table(db: AsyncSession, model, household_id: UUID) -> list[dict]:
    """Export all rows from a table for a household."""
    if not hasattr(model, "household_id"):
        return []
    result = await db.execute(
        select(model).where(model.household_id == household_id)
    )
    return [_serialize_row(row) for row in result.scalars().all()]


@router.get("/data-export")
async def export_data(
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    """
    GDPR data export: returns all household data as JSON.
    Only accessible by the owner.
    """
    if current_member.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alleen de eigenaar kan gegevens exporteren.",
        )

    household_id = current_member.household_id

    # Household
    result = await db.execute(
        select(Household).where(Household.id == household_id)
    )
    household = result.scalar_one_or_none()
    household_data = _serialize_row(household) if household else {}

    # Members
    members_result = await db.execute(
        select(Member).where(Member.household_id == household_id)
    )
    members_data = [
        _serialize_row(m, exclude_fields={"user_id"})
        for m in members_result.scalars().all()
    ]
    member_ids = [m.id for m in members_result.scalars().all()]

    # Re-fetch member_ids properly
    members_result2 = await db.execute(
        select(Member.id).where(Member.household_id == household_id)
    )
    member_ids = [row[0] for row in members_result2.fetchall()]

    export = {
        "export_date": datetime.utcnow().isoformat(),
        "household": household_data,
        "members": members_data,
        "onboarding": await _export_table(db, OnboardingAnswer, household_id),
        "tasks": await _export_table(db, Task, household_id),
        "task_completions": await _export_table(db, TaskCompletion, household_id),
        "calendar_events": await _export_table(db, CalendarEvent, household_id),
        "inventory_items": await _export_table(db, InventoryItem, household_id),
        "inventory_alerts": await _export_table(db, InventoryAlert, household_id),
        "patterns": await _export_table(db, Pattern, household_id),
        "chat_messages": await _export_table(db, ChatMessage, household_id),
        "notification_log": await _export_table(db, NotificationLog, household_id),
        "daycare_contacts": await _export_table(db, DaycareContact, household_id),
        "sync_queue": await _export_table(db, SyncQueueItem, household_id),
    }

    # Notification profiles (linked by member_id, not household_id)
    if member_ids:
        profiles_result = await db.execute(
            select(NotificationProfile).where(
                NotificationProfile.member_id.in_(member_ids)
            )
        )
        export["notification_profiles"] = [
            _serialize_row(p) for p in profiles_result.scalars().all()
        ]

        # Calendar integrations
        integrations_result = await db.execute(
            select(CalendarIntegration).where(
                CalendarIntegration.member_id.in_(member_ids)
            )
        )
        export["calendar_integrations"] = [
            _serialize_row(ci, exclude_fields={"access_token", "refresh_token"})
            for ci in integrations_result.scalars().all()
        ]
    else:
        export["notification_profiles"] = []
        export["calendar_integrations"] = []

    # Subscription
    sub_result = await db.execute(
        select(Subscription).where(Subscription.household_id == household_id)
    )
    sub = sub_result.scalar_one_or_none()
    export["subscription"] = _serialize_row(sub) if sub else None

    logger.info(f"Data export for household {household_id}")
    return JSONResponse(content=export)


@router.delete("")
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    GDPR account deletion: deletes all data for the household including vectors.
    Only accessible by the owner. This action is irreversible.
    """
    if current_member.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alleen de eigenaar kan het account verwijderen.",
        )

    household_id = current_member.household_id

    # Get all member IDs for cleanup of member-linked tables
    members_result = await db.execute(
        select(Member.id).where(Member.household_id == household_id)
    )
    member_ids = [row[0] for row in members_result.fetchall()]

    # Delete member-linked data first
    if member_ids:
        await db.execute(
            delete(NotificationProfile).where(
                NotificationProfile.member_id.in_(member_ids)
            )
        )
        await db.execute(
            delete(CalendarIntegration).where(
                CalendarIntegration.member_id.in_(member_ids)
            )
        )

    # Delete household-linked data (order matters for FK constraints)
    # Vector documents first (no FK dependencies on them)
    await db.execute(
        delete(VectorDocument).where(VectorDocument.household_id == household_id)
    )
    await db.execute(
        delete(ChatMessage).where(ChatMessage.household_id == household_id)
    )
    await db.execute(
        delete(NotificationLog).where(NotificationLog.household_id == household_id)
    )
    await db.execute(
        delete(Pattern).where(Pattern.household_id == household_id)
    )
    await db.execute(
        delete(InventoryAlert).where(InventoryAlert.household_id == household_id)
    )
    await db.execute(
        delete(InventoryItem).where(InventoryItem.household_id == household_id)
    )
    await db.execute(
        delete(TaskCompletion).where(TaskCompletion.household_id == household_id)
    )
    await db.execute(
        delete(CalendarEvent).where(CalendarEvent.household_id == household_id)
    )
    await db.execute(
        delete(Task).where(Task.household_id == household_id)
    )
    await db.execute(
        delete(SyncQueueItem).where(SyncQueueItem.household_id == household_id)
    )
    await db.execute(
        delete(DaycareContact).where(DaycareContact.household_id == household_id)
    )
    await db.execute(
        delete(OnboardingAnswer).where(OnboardingAnswer.household_id == household_id)
    )
    await db.execute(
        delete(Subscription).where(Subscription.household_id == household_id)
    )
    # Members and household last
    await db.execute(
        delete(Member).where(Member.household_id == household_id)
    )
    await db.execute(
        delete(Household).where(Household.id == household_id)
    )

    await db.commit()

    logger.info(f"Account deleted: household {household_id}, user {user_id}")
    return {"status": "deleted", "message": "Alle gegevens zijn verwijderd."}
