from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from models.calendar import CalendarEvent
from models.member import Member, MemberRole
from schemas.calendar import CalendarEventCreate, CalendarEventResponse, CalendarEventUpdate

router = APIRouter()


@router.get("/events", response_model=list[CalendarEventResponse])
async def list_events(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Zorgverleners hebben geen toegang tot de agenda.")

    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.household_id == member.household_id)
            .order_by(CalendarEvent.start_time)
    )
    return result.scalars().all()


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: CalendarEventCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    event = CalendarEvent(
        household_id=member.household_id,
        member_id=payload.member_id or member.id,
        source="manual",
        title=payload.title,
        description=payload.description,
        location=payload.location,
        start_time=payload.start_time,
        end_time=payload.end_time,
        all_day=payload.all_day,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: UUID,
    payload: CalendarEventUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.household_id == member.household_id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.household_id == member.household_id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(event)
    await db.commit()
