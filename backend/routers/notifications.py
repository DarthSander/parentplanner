from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from models.member import Member
from models.notification import NotificationLog, NotificationProfile
from schemas.notification import (
    NotificationLogResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)

router = APIRouter()


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationProfile).where(NotificationProfile.member_id == member.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        # Create default profile
        profile = NotificationProfile(member_id=member.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.patch("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    payload: NotificationPreferencesUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationProfile).where(NotificationProfile.member_id == member.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = NotificationProfile(member_id=member.id)
        db.add(profile)
        await db.flush()

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/history", response_model=list[NotificationLogResponse])
async def get_notification_history(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.member_id == member.id)
        .order_by(NotificationLog.sent_at.desc())
        .limit(50)
    )
    return result.scalars().all()
