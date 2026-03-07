import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.dependencies import get_current_member
from core.encryption import encrypt_token
from core.rate_limiter import limiter
from models.calendar import CalendarEvent, CalendarIntegration
from models.member import Member, MemberRole
from schemas.calendar import (
    CalDAVIntegrationCreate,
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
    CalendarIntegrationResponse,
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
    SyncResult,
)
from services.calendar.google_sync import (
    exchange_code_for_tokens,
    get_google_auth_url,
    get_primary_calendar_id,
    sync_all_integrations,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Calendar Events ───────────────────────────────────────────────────────

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


# ── Calendar Integrations ─────────────────────────────────────────────────

@router.get("/integrations", response_model=list[CalendarIntegrationResponse])
async def list_integrations(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List all calendar integrations for the current member."""
    result = await db.execute(
        select(CalendarIntegration).where(CalendarIntegration.member_id == member.id)
        .order_by(CalendarIntegration.created_at)
    )
    return result.scalars().all()


@router.get("/integrations/google/auth-url", response_model=GoogleAuthUrlResponse)
async def google_auth_url(
    redirect_uri: str,
    member: Member = Depends(get_current_member),
):
    """
    Generate the Google OAuth consent screen URL.
    Frontend redirects the user to this URL to start the OAuth flow.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integratie is niet geconfigureerd op deze server.",
        )

    # State encodes the member ID for verification in the callback
    state = str(member.id)
    try:
        auth_url = get_google_auth_url(redirect_uri=redirect_uri, state=state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return GoogleAuthUrlResponse(auth_url=auth_url)


@router.post(
    "/integrations/google",
    response_model=CalendarIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/hour")
async def connect_google_calendar(
    request: Request,
    payload: GoogleCallbackRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange the OAuth authorization code for tokens and store the integration.
    Called after Google redirects back with ?code=... in the frontend.
    """
    try:
        token_data = await exchange_code_for_tokens(payload.code, payload.redirect_uri)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geen access token ontvangen van Google.")

    # Fetch the primary calendar ID
    try:
        calendar_id = await get_primary_calendar_id(access_token)
    except Exception:
        calendar_id = "primary"

    # Check if integration already exists for this calendar
    existing_result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.member_id == member.id,
            CalendarIntegration.provider == "google",
            CalendarIntegration.external_calendar_id == calendar_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    token_expires_at = now.replace(microsecond=0)
    from datetime import timedelta
    token_expires_at = now + timedelta(seconds=expires_in)

    if existing:
        # Update existing integration with fresh tokens
        existing.access_token = encrypt_token(access_token)
        if refresh_token:
            existing.refresh_token = encrypt_token(refresh_token)
        existing.token_expires_at = token_expires_at
        existing.sync_enabled = True
        await db.commit()
        await db.refresh(existing)
        return existing

    integration = CalendarIntegration(
        member_id=member.id,
        provider="google",
        external_calendar_id=calendar_id,
        access_token=encrypt_token(access_token),
        refresh_token=encrypt_token(refresh_token) if refresh_token else None,
        token_expires_at=token_expires_at,
        sync_enabled=True,
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return integration


@router.post("/integrations/caldav", response_model=CalendarIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def connect_caldav(
    payload: CalDAVIntegrationCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Connect a CalDAV calendar (iCloud, Nextcloud, etc.).
    Credentials are stored encrypted.
    """
    integration = CalendarIntegration(
        member_id=member.id,
        provider="caldav",
        external_calendar_id=payload.calendar_url,
        access_token=encrypt_token(payload.username),
        refresh_token=encrypt_token(payload.password),
        sync_enabled=True,
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return integration


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_integration(
    integration_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Remove a calendar integration and optionally delete synced events."""
    result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.member_id == member.id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Remove synced events for this provider (keep manual events)
    await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.household_id == member.household_id,
            CalendarEvent.member_id == member.id,
            CalendarEvent.source == integration.provider,
        )
    )
    # Delete synced calendar events
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(CalendarEvent).where(
            CalendarEvent.household_id == member.household_id,
            CalendarEvent.member_id == member.id,
            CalendarEvent.source == integration.provider,
        )
    )

    await db.delete(integration)
    await db.commit()


@router.post("/sync", response_model=list[SyncResult])
@limiter.limit("10/hour")
async def sync_calendars(
    request: Request,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a manual sync of all connected calendar integrations.
    Rate limited to 10 per hour to avoid hammering the Google API.
    """
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Zorgverleners kunnen de agenda niet synchroniseren.")

    results = await sync_all_integrations(db, member.household_id, member.id)
    return [SyncResult(**r) for r in results]
