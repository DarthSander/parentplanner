"""
Context Engine — evening cron (20:00).

Processes upcoming calendar events and generates smart tasks per event type:
  - daycare    → luiertas checklist
  - medical    → afspraken voorbereiding
  - birthday   → cadeau kopen, kaartje sturen
  - trip       → daguitje paklijst, weersverwachting, wie gaat er mee?
  - vacation   → volledige reisvoorbereiding gespreid over weken
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.calendar import CalendarEvent
from models.chat import ChatMessage
from models.member import Member
from models.task import Task
from schemas.ai_generated import AIGeneratedTask
from services.ai.ai_utils import AICallError, call_claude, validate_json_list
from services.calendar.event_classifier import (
    classify_event,
    extract_birthday_info,
    extract_destination,
)
from services.vector.retrieval import retrieve_context
from services.weather import get_weather_forecast

logger = logging.getLogger(__name__)


# ── Entrypoint ────────────────────────────────────────────────────────────────

async def process_upcoming_events(db: AsyncSession, household_id: UUID):
    """
    Main entry point called by the calendar_analysis Celery worker.

    Look-ahead windows:
      - 48 hours for daycare/medical (same-day urgency)
      - 21 days for birthdays, trips, vacations (need lead time for prep)
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.household_id == household_id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= now + timedelta(days=21),
            CalendarEvent.ai_context_processed == False,
        )
    )
    events = result.scalars().all()

    if not events:
        return

    members_result = await db.execute(
        select(Member).where(
            Member.household_id == household_id,
            Member.role.in_(["owner", "partner", "caregiver"]),
        )
    )
    members = members_result.scalars().all()

    general_context = await retrieve_context(db, household_id, "kalender taken huishouden gezin")

    for event in events:
        event_type = classify_event(
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
        )
        event.event_type = event_type

        days_until = (event.start_time.date() - now.date()).days

        try:
            if event_type == "daycare" and days_until <= 2:
                await _handle_daycare(db, household_id, event, general_context)
            elif event_type == "medical" and days_until <= 3:
                await _handle_medical(db, household_id, event, general_context)
            elif event_type == "birthday":
                await _handle_birthday(db, household_id, event, members, general_context)
            elif event_type == "trip":
                await _handle_trip(db, household_id, event, members, general_context)
            elif event_type == "vacation":
                await _handle_vacation(db, household_id, event, members, general_context)
        except Exception as e:
            logger.error(
                f"Handler for event {event.id} (type={event_type}) failed: {e}",
                exc_info=True,
            )

        event.ai_context_processed = True

    await db.commit()


# ── Shared helpers ────────────────────────────────────────────────────────────

def _make_task(household_id: UUID, event: CalendarEvent, item: AIGeneratedTask, default_category: str = "household") -> Task:
    """Create a Task linked to its source calendar event."""
    return Task(
        household_id=household_id,
        title=item.title,
        description=item.description,
        category=item.category or default_category,
        task_type=item.task_type or "prep",
        estimated_minutes=item.estimated_minutes,
        due_date=datetime.fromisoformat(item.due_date),
        ai_generated=True,
        linked_calendar_event_id=event.id,
    )


async def _post_chat_message(
    db: AsyncSession,
    household_id: UUID,
    member_id: UUID,
    content: str,
    actions: list[dict] | None = None,
):
    """Insert a proactive AI assistant message into the household chat."""
    body = content
    if actions:
        body += f"\n\n```actions\n{json.dumps(actions, ensure_ascii=False)}\n```"
    db.add(ChatMessage(
        household_id=household_id,
        member_id=member_id,
        role="assistant",
        content=body,
    ))


# ── Daycare ───────────────────────────────────────────────────────────────────

async def _handle_daycare(db, household_id, event, context):
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

Genereer een JSON array van taken. Elk object: title, description, category, task_type, estimated_minutes, due_date (ISO).
Prep-taken: avond voor opvangdag 20:00. Quick-taken: ochtend zelf 07:00.
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
        logger.error(f"Daycare tasks failed for {household_id}: {e}")
        return
    for item in tasks_data:
        db.add(_make_task(household_id, event, item, "baby_care"))


# ── Medical ───────────────────────────────────────────────────────────────────

async def _handle_medical(db, household_id, event, context):
    system_prompt = f"""
Je bent de gezinsassistent. Maak voorbereidingstaken aan voor een medische afspraak.
Denk aan: zorgpasje, vaccinatieboekje, vragen voorbereiden, op tijd vertrekken.

GEZINSCONTEXT:
{chr(10).join(context[:6])}

Genereer een JSON array van taken. Elk object: title, description, category, task_type, estimated_minutes, due_date (ISO).
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
        logger.error(f"Medical tasks failed for {household_id}: {e}")
        return
    for item in tasks_data:
        db.add(_make_task(household_id, event, item, "baby_care"))


# ── Birthday ──────────────────────────────────────────────────────────────────

async def _handle_birthday(db, household_id, event, members, context):
    """Cadeau kopen, kaartje sturen, feestje plannen bij ronde verjaardag."""
    name, age = extract_birthday_info(event.title)
    now = datetime.now(timezone.utc)
    days_until = (event.start_time.date() - now.date()).days

    if days_until < 0 or days_until > 21:
        return

    name_str = f"voor {name}" if name else ""
    age_str = f" ({name} wordt {age})" if age else ""
    is_round = age in {1, 2, 3, 5, 10, 18, 21, 25, 30, 40, 50, 60}
    birthday_label = event.start_time.strftime("%A %d %B %Y")

    cadeau_due = (event.start_time - timedelta(days=max(3, min(days_until - 1, 7)))).strftime("%Y-%m-%dT10:00:00")
    dag_zelf_due = event.start_time.strftime("%Y-%m-%dT09:00:00")

    system_prompt = f"""
Je bent de gezinsassistent. Er is een verjaardag in de agenda{age_str}.
Maak 2-4 passende taken aan.

REGELS:
- Cadeau kopen {name_str}: due_date = {cadeau_due}, task_type = "prep"
- Kaartje/bericht sturen {name_str}: due_date = {dag_zelf_due}, task_type = "quick"
{"- Feestje plannen (ronde verjaardag!): ruim van tevoren" if is_round else ""}
- Benoem naam {name_str} in de taaktitel indien bekend.

GEZINSCONTEXT:
{chr(10).join(context[:6])}

JSON array, elk object: title, description, category, task_type, estimated_minutes, due_date (ISO).
Antwoord alleen met de JSON array.
"""
    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"Verjaardag: {event.title} op {birthday_label}. Nog {days_until} dagen.",
            max_tokens=600,
        )
        tasks_data = validate_json_list(response, AIGeneratedTask)
    except AICallError as e:
        logger.error(f"Birthday tasks failed for {household_id}: {e}")
        return
    for item in tasks_data:
        db.add(_make_task(household_id, event, item, "household"))
    logger.info(f"Birthday: {len(tasks_data)} tasks for '{event.title}' (household {household_id})")


# ── Day trip ──────────────────────────────────────────────────────────────────

async def _handle_trip(db, household_id, event, members, context):
    """Kaartjes, paklijst, weerkleding, baby-items. Proactieve chatmelding: wie gaat mee?"""
    destination = extract_destination(event.title, event.description, event.location)
    trip_date = event.start_time
    days_until = (trip_date.date() - datetime.now(timezone.utc).date()).days

    weather = await get_weather_forecast(destination, trip_date)
    weather_info = weather["summary"] if weather else "Weersvoorspelling niet beschikbaar."

    tickets_due = (trip_date - timedelta(days=max(1, min(days_until - 1, 7)))).strftime("%Y-%m-%dT20:00:00")
    pack_due = (trip_date - timedelta(days=1)).strftime("%Y-%m-%dT20:00:00")
    day_of_due = trip_date.strftime("%Y-%m-%dT07:00:00")

    system_prompt = f"""
Je bent de gezinsassistent. Er is een daguitje gepland naar {destination}.

DATUM: {trip_date.strftime("%A %d %B %Y")}
WEERSVERWACHTING: {weather_info}
GEZINSLEDEN: {", ".join(m.display_name for m in members)}

TAKEN DIE TYPISCH NODIG ZIJN:
- Kaartjes/reservering online regelen: due = {tickets_due}
- Eten & drinken inpakken: due = {pack_due}
- Weer-afhankelijke kleding (zie weersverwachting): due = {pack_due}
- Baby-spullen indien van toepassing (luiers, flesjes, slaapzak): due = {pack_due}
- Vervoer/tankbeurt regelen: due = {pack_due}
- Camera/telefoon opladen: due = {day_of_due}
- Zonnebrand als het warm is

GEZINSCONTEXT:
{chr(10).join(context[:8])}

JSON array, elk object: title, description, category, task_type, estimated_minutes, due_date (ISO).
Antwoord alleen met de JSON array.
"""
    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"Daguitje: {event.title}",
            max_tokens=1200,
        )
        tasks_data = validate_json_list(response, AIGeneratedTask)
    except AICallError as e:
        logger.error(f"Trip tasks failed for {household_id}: {e}")
        return
    for item in tasks_data:
        db.add(_make_task(household_id, event, item, "household"))

    owner = next((m for m in members if m.role.value == "owner"), members[0] if members else None)
    if owner and members:
        actions = [
            {"action": "trip_members_response", "label": m.display_name, "data": {"member_id": str(m.id)}}
            for m in members
        ]
        await _post_chat_message(
            db, household_id, owner.id,
            f"🗺️ Daguitje naar **{destination}** op {trip_date.strftime('%A %d %B')}! "
            f"Ik heb {len(tasks_data)} taken aangemaakt. {weather_info}\n\n"
            "Wie gaan er mee? (Selecteer iedereen die meegaat)",
            actions=actions,
        )
    logger.info(f"Trip: {len(tasks_data)} tasks for '{event.title}' (household {household_id})")


# ── Vacation ──────────────────────────────────────────────────────────────────

async def _handle_vacation(db, household_id, event, members, context):
    """Volledige reisvoorbereiding: administratief, bagage, baby, huis, vervoer."""
    destination = extract_destination(event.title, event.description, event.location)
    departure = event.start_time
    return_date = event.end_time
    duration_nights = max(1, (return_date.date() - departure.date()).days)
    days_until = (departure.date() - datetime.now(timezone.utc).date()).days

    weather = await get_weather_forecast(destination, departure)
    weather_info = weather["summary"] if weather else "Weersvoorspelling nog niet beschikbaar."

    # Staged due dates
    early_due = (departure - timedelta(days=min(days_until - 1, 14))).strftime("%Y-%m-%dT20:00:00")
    week_before = (departure - timedelta(days=7)).strftime("%Y-%m-%dT20:00:00")
    day_before = (departure - timedelta(days=1)).strftime("%Y-%m-%dT20:00:00")
    departure_morning = departure.strftime("%Y-%m-%dT07:00:00")

    system_prompt = f"""
Je bent de gezinsassistent. Er is een vakantie gepland.

BESTEMMING: {destination}
VERTREK: {departure.strftime("%A %d %B %Y")}
TERUG: {return_date.strftime("%A %d %B %Y")} ({duration_nights} nachten)
WEERSVERWACHTING: {weather_info}
GEZINSLEDEN: {", ".join(m.display_name for m in members)}

FASE 1 — ADMINISTRATIEF (2+ weken van tevoren, due={early_due}):
Paspoorten/ID geldigheid, reisverzekering, hotel/vliegtickets, valuta, telefoonbundel

FASE 2 — BABY/KIND + BAGAGE (1 week voor, due={week_before}):
Luiers {duration_nights} dagen + reserve, babyfood, medicijnen, slaapzak baby,
kleding per persoon per dag (weerafgestemd), zonnebrand, regenjas

FASE 3 — HUIS REGELEN (dag voor vertrek, due={day_before}):
Planten water, post stopzetten, koelkast leegmaken, sleutel buren

FASE 4 — VERVOER (dag van vertrek, due={departure_morning}):
Auto nakijken, navigatie, snacks, op tijd vertrekken

GEZINSCONTEXT:
{chr(10).join(context[:8])}

Genereer 12-20 concrete taken verspreid over de fases.
JSON array, elk object: title, description, category, task_type, estimated_minutes, due_date (ISO).
Antwoord alleen met de JSON array.
"""
    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"Vakantie: {event.title}",
            max_tokens=2000,
        )
        tasks_data = validate_json_list(response, AIGeneratedTask)
    except AICallError as e:
        logger.error(f"Vacation tasks failed for {household_id}: {e}")
        return
    for item in tasks_data:
        db.add(_make_task(household_id, event, item, "household"))

    owner = next((m for m in members if m.role.value == "owner"), members[0] if members else None)
    if owner and members:
        actions = [
            {"action": "trip_members_response", "label": m.display_name, "data": {"member_id": str(m.id)}}
            for m in members
        ]
        await _post_chat_message(
            db, household_id, owner.id,
            f"✈️ Vakantie naar **{destination}** staat gepland! "
            f"{departure.strftime('%d %B')} – {return_date.strftime('%d %B')} ({duration_nights} nachten). "
            f"Ik heb {len(tasks_data)} taken aangemaakt, gespreid over de komende weken. "
            f"{weather_info}\n\nWie gaan er mee op vakantie?",
            actions=actions,
        )
    logger.info(f"Vacation: {len(tasks_data)} tasks for '{event.title}' (household {household_id})")
