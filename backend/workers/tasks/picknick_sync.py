"""
Picknick daily sync worker.

Runs every day at 08:00 to:
1. Fetch new order history from Picknick
2. Generate vector embeddings for new orders
3. Update integration last_synced_at timestamp

Only processes households on the family tier with an active Picknick integration.
"""
import asyncio
import logging

from sqlalchemy import select

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.picknick_sync.sync_orders")
def sync_orders():
    asyncio.run(_sync_all())


async def _sync_all():
    from datetime import datetime, timezone

    from core.database import get_db_context
    from models.picknick import PicknickIntegration, PicknickOrderHistory
    from models.subscription import Subscription
    from services.picknick.auth import get_picknick_client_for_integration
    from services.picknick.products import get_order_history

    async with get_db_context() as db:
        # Only family-tier households with active Picknick integration
        result = await db.execute(
            select(PicknickIntegration)
            .join(Subscription, Subscription.household_id == PicknickIntegration.household_id)
            .where(
                PicknickIntegration.sync_enabled == True,
                Subscription.status.in_(["active", "trialing"]),
                Subscription.tier == "family",
            )
        )
        integrations = result.scalars().all()
        logger.info(f"Picknick sync: processing {len(integrations)} integration(s)")

        for integration in integrations:
            try:
                await _sync_integration(db, integration)
            except Exception as e:
                logger.error(f"Picknick sync failed for integration {integration.id}: {e}", exc_info=True)


async def _sync_integration(db, integration):
    from datetime import datetime, timezone

    from models.picknick import PicknickOrderHistory
    from models.vector import VectorDocument
    from services.picknick.auth import get_picknick_client_for_integration
    from services.picknick.products import get_order_history
    from services.vector.embeddings import build_picknick_order_document, generate_embedding

    client = await get_picknick_client_for_integration(integration)
    raw_orders = await get_order_history(client)
    synced = 0

    for raw in raw_orders:
        order_id = str(raw.get("id", ""))
        if not order_id:
            continue

        existing = await db.execute(
            select(PicknickOrderHistory).where(PicknickOrderHistory.picknick_order_id == order_id)
        )
        if existing.scalar_one_or_none():
            continue

        order = PicknickOrderHistory(
            household_id=integration.household_id,
            integration_id=integration.id,
            picknick_order_id=order_id,
            items_json=raw,
        )
        db.add(order)
        await db.flush()  # get order.id

        # Create vector embedding for pattern analysis
        try:
            doc_text = build_picknick_order_document(order)
            embedding = await generate_embedding(doc_text)
            vector_doc = VectorDocument(
                household_id=integration.household_id,
                source_type="picknick_order",
                source_id=order.id,
                content=doc_text,
                embedding=embedding,
            )
            db.add(vector_doc)
        except Exception as e:
            logger.warning(f"Failed to embed Picknick order {order_id}: {e}")

        synced += 1

    integration.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    if synced:
        logger.info(f"Picknick sync: {synced} new orders for household {integration.household_id}")
