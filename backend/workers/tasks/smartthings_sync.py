"""
SmartThings device sync worker.

Polls SmartThings API every 5 minutes to detect device state changes.
This is the fallback mechanism when webhooks are not available.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from core.database import get_db_context
from models.smartthings import SmartThingsDevice, SmartThingsIntegration
from models.subscription import Subscription
from services.smartthings.auth import get_valid_access_token
from services.smartthings.devices import detect_cycle_change, fetch_device_status
from services.smartthings.events import process_cycle_completed, process_cycle_started
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.smartthings_sync.sync_all")
def sync_all():
    """Sync all active SmartThings integrations."""
    asyncio.run(_sync_all())


async def _sync_all():
    async with get_db_context() as db:
        # Only process households with active family tier subscriptions
        result = await db.execute(
            select(SmartThingsIntegration)
            .join(
                Subscription,
                Subscription.household_id == SmartThingsIntegration.household_id,
            )
            .where(
                SmartThingsIntegration.sync_enabled == True,
                Subscription.status.in_(["active", "trialing"]),
                Subscription.tier == "family",
            )
        )
        integrations = result.scalars().all()

        for integration in integrations:
            try:
                await _sync_integration_devices(db, integration)
            except Exception as e:
                logger.error(
                    f"SmartThings sync failed for household {integration.household_id}: {e}"
                )


async def _sync_integration_devices(db, integration: SmartThingsIntegration):
    """Poll status of all devices for an integration and detect changes."""
    try:
        access_token = await get_valid_access_token(db, integration)
    except Exception as e:
        logger.error(f"Failed to get access token for integration {integration.id}: {e}")
        return

    devices_result = await db.execute(
        select(SmartThingsDevice).where(
            SmartThingsDevice.integration_id == integration.id,
            SmartThingsDevice.sync_enabled == True,
        )
    )
    devices = devices_result.scalars().all()

    for device in devices:
        try:
            new_status = await fetch_device_status(access_token, device.external_device_id)

            # Detect cycle changes
            change = detect_cycle_change(device, new_status)

            if change == "cycle_started":
                await process_cycle_started(db, device)
            elif change == "cycle_completed":
                await process_cycle_completed(db, device)

            # Update stored state
            device.current_state = new_status
            device.updated_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.warning(f"Failed to sync device {device.label}: {e}")

    integration.last_synced_at = datetime.now(timezone.utc)
    await db.commit()
