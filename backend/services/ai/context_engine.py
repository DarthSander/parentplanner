import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.calendar import CalendarEvent
from models.task import Task
from schemas.ai_generated import AIGeneratedTask
from services.ai.ai_utils import AICallError, call_claude, validate_json_list
from services.vector.retrieval import retrieve_context

logger = logging.getLogger(__name__)

DAYCARE_KEYWORDS = ["opvang", "dagopvang", "kinderopvang", "crèche", "bso"]
CHECKUP_KEYWORDS = ["consultatieburo", "huisarts", "prikken", "vaccinatie"]


async def process_upcoming_events(db: AsyncSession, household_id: UUID):
    """Process calendar events for the next 48 hours and generate tasks."""
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)

    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.household_id == household_id,
            CalendarEvent.start_time >= tomorrow,
            CalendarEvent.start_time <= day_after,
            CalendarEvent.ai_context_processed == False,
        )
    )
    events = result.scalars().all()

    context_docs = await retrieve_context(db, household_id, "kalender opvang taken morgen")

    for event in events:
        event_lower = event.title.lower()

        if any(kw in event_lower for kw in DAYCARE_KEYWORDS):
            await _generate_daycare_tasks(db, household_id, event, context_docs)

        if any(kw in event_lower for kw in CHECKUP_KEYWORDS):
            await _generate_checkup_tasks(db, household_id, event, context_docs)

        event.ai_context_processed = True

    await db.commit()


async def _generate_daycare_tasks(db, household_id, event, context):
    system_prompt = f"""
Je bent de gezinsassistent. Maak concrete taken aan voor de opvangdag.

STANDAARD LUIERTASLIJST:
- Luiers inpakken (minimaal 4 stuks)
- Reservekleding inpakken (2 sets)
- Slaapzakje controleren
- Flesjes vullen of melkpoeder afmeten
- Speentje
- Naam op alle spullen checken
- Avond ervoor tas klaarzetten

GEZINSCONTEXT:
{chr(10).join(context[:8])}

Genereer een JSON array van taken. Elk object heeft: title, description, category, task_type, estimated_minutes, due_date (ISO string).
De due_date is de avond voor de opvangdag (20:00) voor prep-taken en de ochtend zelf (07:00) voor quick-taken.
Antwoord alleen met de JSON array.
"""
    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"Opvangdag: {event.start_time.strftime('%A %d %B %Y')}. Eventnaam: {event.title}",
            max_tokens=1000,
        )
        tasks_data = validate_json_list(response, AIGeneratedTask)
    except AICallError as e:
        logger.error(f"Failed to parse daycare tasks for household {household_id}: {e}")
        return

    for task_item in tasks_data:
        task = Task(
            household_id=household_id,
            title=task_item.title,
            description=task_item.description,
            category=task_item.category,
            task_type=task_item.task_type,
            estimated_minutes=task_item.estimated_minutes,
            due_date=datetime.fromisoformat(task_item.due_date),
            ai_generated=True,
        )
        db.add(task)


async def _generate_checkup_tasks(db, household_id, event, context):
    system_prompt = f"""
Je bent de gezinsassistent. Maak concrete voorbereidingstaken aan voor een medische afspraak.

Denk aan:
- Zorgpasje/verzekeringsbewijs meenemen
- Vaccinatieboekje meenemen
- Vragen voorbereiden
- Op tijd vertrekken

GEZINSCONTEXT:
{chr(10).join(context[:6])}

Genereer een JSON array van taken. Elk object heeft: title, description, category, task_type, estimated_minutes, due_date (ISO string).
Antwoord alleen met de JSON array.
"""
    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"Afspraak: {event.title} op {event.start_time.strftime('%A %d %B %Y om %H:%M')}",
            max_tokens=500,
        )
        tasks_data = validate_json_list(response, AIGeneratedTask)
    except AICallError as e:
        logger.error(f"Failed to parse checkup tasks for household {household_id}: {e}")
        return

    for task_item in tasks_data:
        task = Task(
            household_id=household_id,
            title=task_item.title,
            description=task_item.description,
            category="baby_care",
            task_type=task_item.task_type,
            estimated_minutes=task_item.estimated_minutes,
            due_date=datetime.fromisoformat(task_item.due_date),
            ai_generated=True,
        )
        db.add(task)
