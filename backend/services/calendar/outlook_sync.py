"""
Microsoft Outlook / Office 365 calendar integration via Microsoft Graph API.

OAuth flow (Microsoft Identity Platform v2.0):
  1. GET /calendar/integrations/outlook/auth-url  → redirect user to Microsoft login
  2. Microsoft redirects to callback with ?code=...
  3. POST /calendar/integrations/outlook          → exchange code for tokens, store encrypted
  4. POST /calendar/sync                          → fetch events via Graph API, upsert to DB

Docs: https://learn.microsoft.com/en-us/graph/api/user-list-events
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

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_API = "https://graph.microsoft.com/v1.0"
SCOPES = ["Calendars.ReadWrite", "offline_access", "User.Read"]


def get_outlook_auth_url(redirect_uri: str, state: str) -> str:
    """Generate Microsoft OAuth consent screen URL."""
    if not settings.MICROSOFT_CLIENT_ID:
        raise ValueError("MICROSOFT_CLIENT_ID is niet geconfigureerd")

    scope = " ".join(SCOPES)
    params = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": scope,
        "state": state,
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{MICROSOFT_AUTH_URL}?{query_string}"


async def exchange_code_for_tokens_outlook(code: str, redirect_uri: str) -> dict:
    """Exchange Microsoft authorization code for access + refresh tokens."""
    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        raise ValueError("Microsoft OAuth credentials niet geconfigureerd")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            MICROSOFT_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "scope": " ".join(SCOPES),
            },
        )
        if response.status_code != 200:
            logger.error(f"Outlook token exchange failed: {response.text}")
            raise ValueError(
                f"Token uitwisseling mislukt: {response.json().get('error_description', 'Onbekende fout')}"
            )
        return response.json()


async def _refresh_outlook_token(integration: CalendarIntegration) -> str:
    """Refresh the Outlook access token using the stored refresh token."""
    refresh_token = decrypt_token(integration.refresh_token)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MICROSOFT_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "scope": " ".join(SCOPES),
            },
        )
        if response.status_code != 200:
            raise ValueError("Outlook access token vernieuwen mislukt")
        return response.json()["access_token"]


async def _get_valid_outlook_token(db: AsyncSession, integration: CalendarIntegration) -> str:
    """Return a valid Outlook access token, refreshing if needed."""
    now = datetime.now(timezone.utc)
    if (
        integration.token_expires_at
        and integration.token_expires_at.replace(tzinfo=timezone.utc) > now + timedelta(minutes=5)
    ):
        return decrypt_token(integration.access_token)

    new_token = await _refresh_outlook_token(integration)
    integration.access_token = encrypt_token(new_token)
    integration.token_expires_at = now + timedelta(hours=1)
    await db.commit()
    return new_token


async def _get_primary_calendar_id_outlook(access_token: str) -> str:
    """Get the user's default Outlook calendar ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GRAPH_API}/me/calendar",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code == 200:
            return response.json().get("id", "primary")
    return "primary"


def _parse_outlook_datetime(dt_data: dict) -> tuple[datetime, bool]:
    """Parse Microsoft Graph dateTime object. Returns (datetime, is_all_day)."""
    date_str = dt_data.get("dateTime", "")
    if date_str:
        # Graph returns UTC datetime strings like "2026-03-15T14:00:00.0000000"
        dt = datetime.fromisoformat(date_str.split(".")[0]).replace(tzinfo=timezone.utc)
        return dt, False
    # All-day: only "date" present (as top-level field in Graph events)
    return datetime.now(timezone.utc), True


async def sync_outlook_calendar(
    db: AsyncSession,
    integration: CalendarIntegration,
    household_id: UUID,
    member_id: UUID,
) -> dict:
    """Sync Outlook calendar events for the next 60 days."""
    if not integration.sync_enabled:
        return {"created": 0, "updated": 0, "skipped": 0}

    try:
        access_token = await _get_valid_outlook_token(db, integration)
    except ValueError as e:
        logger.error(f"Cannot sync Outlook calendar {integration.id}: {e}")
        return {"created": 0, "updated": 0, "skipped": 0, "error": str(e)}

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_max = (now + timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

    calendar_id = integration.external_calendar_id

    # Graph API: list events with time range filter
    url = f"{GRAPH_API}/me/calendars/{calendar_id}/events"
    params = {
        "$filter": f"start/dateTime ge '{time_min}' and start/dateTime le '{time_max}'",
        "$select": "id,subject,body,location,start,end,isAllDay,isCancelled",
        "$top": 250,
        "$orderby": "start/dateTime",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            if response.status_code != 200:
                logger.error(f"Graph API error: {response.status_code} {response.text[:200]}")
                return {"created": 0, "updated": 0, "skipped": 0, "error": f"Graph API {response.status_code}"}
            raw_events = response.json().get("value", [])
    except Exception as e:
        logger.error(f"Outlook sync request failed: {e}")
        return {"created": 0, "updated": 0, "skipped": 0, "error": str(e)}

    created = updated = skipped = 0

    for raw in raw_events:
        if raw.get("isCancelled", False):
            skipped += 1
            continue

        external_id = raw.get("id")
        if not external_id:
            skipped += 1
            continue

        is_all_day = raw.get("isAllDay", False)
        try:
            if is_all_day:
                # All-day events use "date" in start/end
                start_str = raw["start"].get("dateTime", "")
                end_str = raw["end"].get("dateTime", "")
                start_dt = datetime.fromisoformat(start_str.split("T")[0]).replace(tzinfo=timezone.utc)
                end_dt = datetime.fromisoformat(end_str.split("T")[0]).replace(tzinfo=timezone.utc)
            else:
                start_dt, _ = _parse_outlook_datetime(raw.get("start", {}))
                end_dt, _ = _parse_outlook_datetime(raw.get("end", {}))
        except (ValueError, KeyError):
            skipped += 1
            continue

        title = raw.get("subject", "(Geen titel)")
        description = (raw.get("body", {}) or {}).get("content", "")
        # Strip HTML from body (basic)
        if description and "<" in description:
            import re
            description = re.sub(r"<[^>]+>", "", description).strip()[:2000]
        location_obj = raw.get("location", {}) or {}
        location = location_obj.get("displayName") or None

        existing_result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.household_id == household_id,
                CalendarEvent.external_id == external_id,
                CalendarEvent.source == "outlook",
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            if (
                existing.title != title
                or existing.start_time != start_dt
                or existing.end_time != end_dt
                or existing.description != description
                or existing.location != location
            ):
                existing.title = title
                existing.description = description or None
                existing.location = location
                existing.start_time = start_dt
                existing.end_time = end_dt
                existing.all_day = is_all_day
                updated += 1
            else:
                skipped += 1
        else:
            event = CalendarEvent(
                household_id=household_id,
                member_id=member_id,
                external_id=external_id,
                source="outlook",
                title=title,
                description=description or None,
                location=location,
                start_time=start_dt,
                end_time=end_dt,
                all_day=is_all_day,
                ai_context_processed=False,
            )
            db.add(event)
            created += 1

    integration.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(
        f"Outlook sync for integration {integration.id}: "
        f"created={created} updated={updated} skipped={skipped}"
    )
    return {"created": created, "updated": updated, "skipped": skipped}


async def write_task_completion_to_outlook(
    db: AsyncSession,
    event: CalendarEvent,
    task_title: str,
    member_name: str,
    completed_at: datetime,
) -> bool:
    """Write a task-completion note back to an Outlook calendar event body."""
    if not event.member_id or not event.external_id:
        return False

    result = await db.execute(
        select(CalendarIntegration).where(
            CalendarIntegration.member_id == event.member_id,
            CalendarIntegration.provider == "outlook",
            CalendarIntegration.sync_enabled == True,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        return False

    try:
        access_token = await _get_valid_outlook_token(db, integration)
    except ValueError:
        return False

    note = (
        f"✓ {task_title} — gedaan door {member_name} op "
        f"{completed_at.strftime('%d %B %Y')}"
    )
    calendar_id = integration.external_calendar_id

    async with httpx.AsyncClient() as client:
        get_resp = await client.get(
            f"{GRAPH_API}/me/calendars/{calendar_id}/events/{event.external_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"$select": "body"},
        )
        if get_resp.status_code != 200:
            return False

        current_body = get_resp.json().get("body", {})
        current_content = current_body.get("content", "")
        content_type = current_body.get("contentType", "text")
        new_content = f"{current_content}\n\n{note}".strip()

        patch_resp = await client.patch(
            f"{GRAPH_API}/me/calendars/{calendar_id}/events/{event.external_id}",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"body": {"contentType": content_type, "content": new_content}},
        )
        if patch_resp.status_code not in (200, 204):
            logger.warning(f"Outlook event patch failed: {patch_resp.status_code}")
            return False

    logger.info(f"Write-back to Outlook event {event.external_id}: {note}")
    return True
