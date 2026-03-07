import logging

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.calendar import CalendarIntegration
from services.calendar.google_sync import sync_google_calendar

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    # TODO: Implement Stripe webhook processing (step 15)
    body = await request.body()
    logger.info(f"Stripe webhook received: {len(body)} bytes")
    return {"received": True}


@router.post("/calendar")
async def calendar_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_goog_channel_id: str | None = Header(None, alias="X-Goog-Channel-ID"),
    x_goog_resource_state: str | None = Header(None, alias="X-Goog-Resource-State"),
    x_goog_resource_id: str | None = Header(None, alias="X-Goog-Resource-ID"),
):
    """
    Handle Google Calendar push notification webhooks.

    Google sends a POST when a calendar changes. The X-Goog-Channel-ID
    header identifies which integration to sync. We use external_calendar_id
    as the channel ID when registering the watch.

    Resource states:
      - sync: initial confirmation (ignore)
      - exists: something changed (trigger sync)
    """
    if x_goog_resource_state == "sync":
        # Initial handshake — just acknowledge
        return {"received": True}

    if not x_goog_resource_id:
        return {"received": True}

    logger.info(
        f"Google Calendar webhook: channel={x_goog_channel_id} "
        f"resource={x_goog_resource_id} state={x_goog_resource_state}"
    )

    # Find the integration by channel ID (we use external_calendar_id as channel ID)
    if x_goog_channel_id:
        result = await db.execute(
            select(CalendarIntegration).where(
                CalendarIntegration.external_calendar_id == x_goog_channel_id,
                CalendarIntegration.provider == "google",
                CalendarIntegration.sync_enabled == True,
            )
        )
        integration = result.scalar_one_or_none()

        if integration:
            # Trigger a sync for this integration
            # We need household_id and member_id — get from member relation
            from models.member import Member
            member_result = await db.execute(
                select(Member).where(Member.id == integration.member_id)
            )
            member = member_result.scalar_one_or_none()

            if member:
                try:
                    sync_result = await sync_google_calendar(
                        db, integration, member.household_id, member.id
                    )
                    logger.info(f"Webhook-triggered sync complete: {sync_result}")
                except Exception as e:
                    logger.error(f"Webhook-triggered sync failed: {e}")

    return {"received": True}
