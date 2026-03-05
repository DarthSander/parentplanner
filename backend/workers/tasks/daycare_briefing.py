import asyncio
import logging
from datetime import datetime, timezone

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.daycare_briefing.send_briefings")
def send_briefings():
    """Morning cron: send daycare briefings."""
    asyncio.run(_send())


async def _send():
    from sqlalchemy import select

    from core.database import get_db_context
    from models.daycare import DaycareContact
    from services.ai.briefing_generator import generate_daycare_briefing
    from services.notification.email import send_email
    from services.notification.whatsapp import send_whatsapp_message

    today = datetime.now(timezone.utc)
    day_name = today.strftime("%A").lower()

    async with get_db_context() as db:
        result = await db.execute(
            select(DaycareContact).where(
                DaycareContact.active == True,
            )
        )
        contacts = result.scalars().all()

        for contact in contacts:
            # Check if today is a briefing day
            if contact.briefing_days and day_name not in [d.lower() for d in contact.briefing_days]:
                continue

            briefing_text = await generate_daycare_briefing(
                db, contact.household_id, contact.name, today
            )
            if not briefing_text:
                continue

            if contact.briefing_channel == "whatsapp" and contact.phone:
                success = await send_whatsapp_message(contact.phone, briefing_text)
                if not success and contact.email:
                    await send_email(
                        to=contact.email,
                        subject=f"Dagbriefing {today.strftime('%d %B')}",
                        html=f"<pre>{briefing_text}</pre>",
                    )
            elif contact.briefing_channel == "email" and contact.email:
                await send_email(
                    to=contact.email,
                    subject=f"Dagbriefing {today.strftime('%d %B')}",
                    html=f"<pre>{briefing_text}</pre>",
                )

            logger.info(f"Briefing sent to {contact.name} ({contact.briefing_channel})")
