import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.calendar_analysis.run")
def run():
    """Evening cron: analyze calendar events for the next 48 hours."""
    asyncio.run(_run())


async def _run():
    from sqlalchemy import select

    from core.database import get_db_context
    from models.household import Household
    from models.subscription import Subscription
    from services.ai.context_engine import process_upcoming_events

    async with get_db_context() as db:
        # Only process households with active AI features
        result = await db.execute(
            select(Household.id).join(
                Subscription, Subscription.household_id == Household.id
            ).where(
                Subscription.status.in_(["active", "trialing"]),
                Subscription.tier.in_(["standard", "family"]),
            )
        )
        household_ids = [row[0] for row in result.fetchall()]

        for hid in household_ids:
            try:
                await process_upcoming_events(db, hid)
                logger.info(f"Calendar analysis completed for household {hid}")
            except Exception as e:
                logger.error(f"Calendar analysis failed for household {hid}: {e}")
