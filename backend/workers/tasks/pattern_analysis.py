import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.pattern_analysis.run")
def run():
    """Weekly cron: analyze task patterns for all active households."""
    asyncio.run(_run())


async def _run():
    from sqlalchemy import select

    from core.database import get_db_context
    from models.household import Household
    from models.subscription import Subscription
    from services.ai.pattern_engine import analyze_patterns

    async with get_db_context() as db:
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
                await analyze_patterns(db, hid)
                logger.info(f"Pattern analysis completed for household {hid}")
            except Exception as e:
                logger.error(f"Pattern analysis failed for household {hid}: {e}")
