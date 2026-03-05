import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.notification_sender.send_morning_reminders")
def send_morning_reminders():
    """Morning cron: send task reminders."""
    asyncio.run(_send_reminders("morning"))


@celery_app.task(name="workers.tasks.notification_sender.send_evening_reminders")
def send_evening_reminders():
    """Evening cron: send task reminders."""
    asyncio.run(_send_reminders("evening"))


@celery_app.task(name="workers.tasks.notification_sender.update_response_rates")
def update_response_rates():
    """Nightly cron: update notification response rates."""
    asyncio.run(_update_rates())


async def _send_reminders(time_of_day: str):
    from datetime import datetime, timezone

    from sqlalchemy import select

    from core.database import get_db_context
    from models.member import Member
    from models.notification import NotificationProfile
    from models.task import Task, TaskStatus

    async with get_db_context() as db:
        # Get tasks due today that are still open
        result = await db.execute(
            select(Task).where(
                Task.status.in_([TaskStatus.open, TaskStatus.in_progress]),
                Task.due_date is not None,
                Task.assigned_to is not None,
            )
        )
        tasks = result.scalars().all()

        for task in tasks:
            # Get member notification profile
            member_result = await db.execute(select(Member).where(Member.id == task.assigned_to))
            member = member_result.scalar_one_or_none()
            if not member:
                continue

            profile_result = await db.execute(
                select(NotificationProfile).where(NotificationProfile.member_id == member.id)
            )
            profile = profile_result.scalar_one_or_none()
            if not profile:
                continue

            # TODO: Implement smart reminder scheduling with quiet hours,
            # escalation, and channel selection (step 9 - FCM push)
            logger.info(f"Reminder for task '{task.title}' to {member.display_name}")


async def _update_rates():
    logger.info("Updating notification response rates")
    # TODO: Calculate response rates based on notification_log
