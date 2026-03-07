"""
Google Calendar OAuth2 integration and sync service.

OAuth flow:
  1. GET /calendar/integrations/google/auth-url  → redirect user to Google
  2. Google redirects to callback with ?code=...
  3. POST /calendar/integrations/google/callback  → exchange code for tokens, store encrypted
  4. POST /calendar/sync                           → fetch events, upsert to calendar_events
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.encryption import decrypt_token, encrypt_token
from models.calendar import CalendarEvent, CalendarIntegration

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_google_auth_url(redirect_uri: str, state: str) -> str:
    """Generate Google OAuth consent screen URL."""
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is niet geconfigureerd")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query_string}"


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials niet geconfigureerd")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise ValueError(f"Token uitwisseling mislukt: {response.json().get('error_description', 'Onbekende fout')}")

        return response.json()


async def refresh_access_token(integration: CalendarIntegration) -> str:
    """Refresh the access token using the stored refresh token."""
    if not integration.refresh_token:
        raise ValueError("Geen refresh token beschikbaar")

    refresh_token = decrypt_token(integration.refresh_token)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
        )
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise ValueError("Access token vernieuwen mislukt")

        data = response.json()
        return data["access_token"]


async def get_valid_access_token(db: AsyncSession, integration: CalendarIntegration) -> str:
    """Return a valid access token, refreshing if needed."""
    now = datetime.now(timezone.utc)
    expires_at = integration.token_expires_at

    # Check if token expires within 5 minutes
    if expires_at and expires_at.replace(tzinfo=timezone.utc) > now + timedelta(minutes=5):
        return decrypt_token(integration.access_token)

    # Refresh token
    logger.info(f"Refreshing access token for integration {integration.id}")
    new_access_token = await refresh_access_token(integration)

    integration.access_token = encrypt_token(new_access_token)
    integration.token_expires_at = now + timedelta(hours=1)
    await db.commit()

    return new_access_token


async def get_primary_calendar_id(access_token: str) -> str:
    """Fetch the user's primary Google Calendar ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GOOGLE_CALENDAR_API}/users/me/calendarList/primary",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            return "primary"
        data = response.json()
        return data.get("id", "primary")


async def fetch_google_events(
    access_token: str,
    calendar_id: str,
    time_min: datetime,
    time_max: datetime,
) -> list[dict]:
    """Fetch events from Google Calendar API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GOOGLE_CALENDAR_API}/calendars/{calendar_id}/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": "250",
            },
        )
        if response.status_code != 200:
            logger.error(f"Google Calendar API error: {response.status_code} {response.text}")
            raise ValueError(f"Google Calendar API fout: {response.status_code}")

        data = response.json()
        return data.get("items", [])


def _parse_google_datetime(dt_data: dict) -> tuple[datetime, bool]:
    """Parse Google Calendar datetime (handles all-day and timed events)."""
    if "dateTime" in dt_data:
        dt = datetime.fromisoformat(dt_data["dateTime"].replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc), False
    elif "date" in dt_data:
        # All-day event
        d = datetime.fromisoformat(dt_data["date"])
        return d.replace(tzinfo=timezone.utc), True
    raise ValueError(f"Onbekend datetime formaat: {dt_data}")


async def sync_google_calendar(
    db: AsyncSession,
    integration: CalendarIntegration,
    household_id: UUID,
    member_id: UUID,
) -> dict:
    """
    Sync Google Calendar events for the next 60 days.
    Returns a dict with counts: {created, updated, skipped}.
    """
    if not integration.sync_enabled:
        return {"created": 0, "updated": 0, "skipped": 0}

    try:
        access_token = await get_valid_access_token(db, integration)
    except ValueError as e:
        logger.error(f"Cannot sync calendar {integration.id}: {e}")
        return {"created": 0, "updated": 0, "skipped": 0, "error": str(e)}

    now = datetime.now(timezone.utc)
    time_min = now - timedelta(days=7)   # include past week for context
    time_max = now + timedelta(days=60)  # sync 60 days ahead

    try:
        raw_events = await fetch_google_events(
            access_token,
            integration.external_calendar_id,
            time_min,
            time_max,
        )
    except ValueError as e:
        logger.error(f"Failed to fetch Google events: {e}")
        return {"created": 0, "updated": 0, "skipped": 0, "error": str(e)}

    created = updated = skipped = 0

    for raw in raw_events:
        # Skip cancelled events
        if raw.get("status") == "cancelled":
            skipped += 1
            continue

        external_id = raw.get("id")
        if not external_id:
            skipped += 1
            continue

        try:
            start_dt, all_day = _parse_google_datetime(raw.get("start", {}))
            end_dt, _ = _parse_google_datetime(raw.get("end", {}))
        except (ValueError, KeyError):
            skipped += 1
            continue

        # Check if event already exists
        existing_result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.household_id == household_id,
                CalendarEvent.external_id == external_id,
                CalendarEvent.source == "google",
            )
        )
        existing = existing_result.scalar_one_or_none()

        title = raw.get("summary", "(Geen titel)")
        description = raw.get("description")
        location = raw.get("location")

        if existing:
            # Update if changed
            if (
                existing.title != title
                or existing.start_time != start_dt
                or existing.end_time != end_dt
                or existing.description != description
                or existing.location != location
            ):
                existing.title = title
                existing.description = description
                existing.location = location
                existing.start_time = start_dt
                existing.end_time = end_dt
                existing.all_day = all_day
                updated += 1
            else:
                skipped += 1
        else:
            event = CalendarEvent(
                household_id=household_id,
                member_id=member_id,
                external_id=external_id,
                source="google",
                title=title,
                description=description,
                location=location,
                start_time=start_dt,
                end_time=end_dt,
                all_day=all_day,
                ai_context_processed=False,
            )
            db.add(event)
            created += 1

    integration.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(
        f"Google Calendar sync for integration {integration.id}: "
        f"created={created} updated={updated} skipped={skipped}"
    )
    return {"created": created, "updated": updated, "skipped": skipped}


async def sync_all_integrations(
    db: AsyncSession,
    household_id: UUID,
    member_id: UUID,
) -> list[dict]:
    """Sync all active integrations for a member."""
    result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.member_id == member_id,
            CalendarIntegration.sync_enabled == True,
        )
    )
    integrations = result.scalars().all()

    results = []
    for integration in integrations:
        if integration.provider == "google":
            sync_result = await sync_google_calendar(db, integration, household_id, member_id)
        elif integration.provider == "outlook":
            from services.calendar.outlook_sync import sync_outlook_calendar
            sync_result = await sync_outlook_calendar(db, integration, household_id, member_id)
        else:
            sync_result = {"created": 0, "updated": 0, "skipped": 0, "note": f"Provider {integration.provider} niet ondersteund"}
        sync_result["integration_id"] = str(integration.id)
        sync_result["provider"] = integration.provider
        results.append(sync_result)

    return results


async def write_task_completion_to_google(
    db: AsyncSession,
    event: "CalendarEvent",
    task_title: str,
    member_name: str,
    completed_at: datetime,
) -> bool:
    """
    Write a task-completion note back to the linked Google Calendar event description.
    E.g. adds: "✓ Cadeau gekocht voor Sara — gedaan door Jan op 5 maart"

    Returns True on success, False on failure.
    """
    from sqlalchemy import select as sa_select
    from models.member import Member

    # Find the Google integration for the event owner (member_id of the event)
    if not event.member_id:
        return False

    result = await db.execute(
        sa_select(CalendarIntegration).where(
            CalendarIntegration.member_id == event.member_id,
            CalendarIntegration.provider == "google",
            CalendarIntegration.sync_enabled == True,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration or not event.external_id:
        return False

    try:
        access_token = await get_valid_access_token(db, integration)
    except ValueError:
        return False

    note = (
        f"✓ {task_title} — gedaan door {member_name} op "
        f"{completed_at.strftime('%d %B %Y')}"
    )

    # Fetch current event description
    async with httpx.AsyncClient() as client:
        get_resp = await client.get(
            f"{GOOGLE_CALENDAR_API}/calendars/{integration.external_calendar_id}/events/{event.external_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if get_resp.status_code != 200:
            logger.warning(f"Could not fetch Google event {event.external_id}: {get_resp.status_code}")
            return False

        current = get_resp.json()
        current_desc = current.get("description", "") or ""
        new_desc = f"{current_desc}\n\n{note}".strip()

        patch_resp = await client.patch(
            f"{GOOGLE_CALENDAR_API}/calendars/{integration.external_calendar_id}/events/{event.external_id}",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"description": new_desc},
        )
        if patch_resp.status_code not in (200, 204):
            logger.warning(f"Google event patch failed: {patch_resp.status_code}")
            return False

    logger.info(f"Write-back to Google Calendar event {event.external_id}: {note}")
    return True
