import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.rate_limiter import limiter
from models.calendar import CalendarEvent
from models.chat import ChatMessage
from models.inventory import InventoryItem
from models.member import Member
from models.onboarding import OnboardingAnswer
from models.pattern import Pattern
from models.task import Task, TaskCompletion
from schemas.chat import ChatMessageResponse, ChatRequest, ChatResponse
from services.ai.ai_utils import AICallError, call_claude

logger = logging.getLogger(__name__)

router = APIRouter()


async def _build_full_context(db: AsyncSession, household_id, member: Member) -> str:
    """Build rich context from all household data for AI conversations."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = today_start + timedelta(days=2)

    # Onboarding / gezinssituatie
    onboarding_result = await db.execute(
        select(OnboardingAnswer).where(OnboardingAnswer.household_id == household_id)
    )
    onboarding = onboarding_result.scalar_one_or_none()

    # Alle gezinsleden
    members_result = await db.execute(
        select(Member).where(Member.household_id == household_id)
    )
    all_members = members_result.scalars().all()
    member_map = {str(m.id): m.display_name for m in all_members}

    # Open taken
    tasks_result = await db.execute(
        select(Task)
        .where(Task.household_id == household_id, Task.status.in_(["open", "in_progress", "snoozed"]))
        .order_by(Task.due_date.asc().nullslast())
        .limit(30)
    )
    open_tasks = tasks_result.scalars().all()

    today_tasks = [t for t in open_tasks if t.due_date and today_start <= t.due_date < tomorrow_end]
    overdue_tasks = [t for t in open_tasks if t.due_date and t.due_date < now]

    # Recente completions afgelopen 7 dagen
    week_ago = now - timedelta(days=7)
    completions_result = await db.execute(
        select(TaskCompletion, Task)
        .join(Task, TaskCompletion.task_id == Task.id)
        .where(TaskCompletion.household_id == household_id, TaskCompletion.completed_at >= week_ago)
        .order_by(TaskCompletion.completed_at.desc())
        .limit(20)
    )
    recent_completions = completions_result.all()

    # Voorraad
    inventory_result = await db.execute(
        select(InventoryItem).where(InventoryItem.household_id == household_id)
    )
    all_items = inventory_result.scalars().all()
    low_stock = [i for i in all_items if i.current_quantity <= i.threshold_quantity]
    out_of_stock = [i for i in all_items if i.current_quantity == 0]

    # Agenda komende 48 uur
    events_result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.household_id == household_id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= now + timedelta(hours=48),
        )
        .order_by(CalendarEvent.start_time)
        .limit(10)
    )
    upcoming_events = events_result.scalars().all()

    # Patronen
    patterns_result = await db.execute(
        select(Pattern)
        .where(Pattern.household_id == household_id)
        .order_by(Pattern.confidence_score.desc())
        .limit(5)
    )
    patterns = patterns_result.scalars().all()

    # Build context string
    parts = []

    if onboarding and onboarding.ai_generated_summary:
        parts.append(f"GEZINSSITUATIE:\n{onboarding.ai_generated_summary}")

    parts.append("GEZINSLEDEN:\n" + "\n".join(
        f"  {m.display_name} (rol: {m.role.value})" for m in all_members if m.role.value != "daycare"
    ))

    if today_tasks:
        parts.append("TAKEN VANDAAG/MORGEN:\n" + "\n".join(
            f"  - {t.title} ({t.category.value})"
            + (f" [toegewezen aan {member_map.get(str(t.assigned_to), '?')}]" if t.assigned_to else " [niet toegewezen]")
            + (f" deadline: {t.due_date.strftime('%d %b %H:%M')}" if t.due_date else "")
            for t in today_tasks
        ))

    if overdue_tasks:
        parts.append("VERLOPEN TAKEN:\n" + "\n".join(
            f"  - {t.title} ({t.snooze_count}x uitgesteld)"
            + (f" [toegewezen aan {member_map.get(str(t.assigned_to), '?')}]" if t.assigned_to else "")
            for t in overdue_tasks[:5]
        ))

    all_open_summary = f"TOTAAL OPEN TAKEN: {len(open_tasks)}"
    if open_tasks:
        by_cat = {}
        for t in open_tasks:
            by_cat.setdefault(t.category.value, 0)
            by_cat[t.category.value] += 1
        all_open_summary += " (" + ", ".join(f"{v} {k}" for k, v in by_cat.items()) + ")"
    parts.append(all_open_summary)

    # Taakverdeling
    dist_lines = []
    for m in all_members:
        if m.role.value == "daycare":
            continue
        count = sum(1 for c, _ in recent_completions if c.completed_by == m.id)
        open_count = sum(1 for t in open_tasks if t.assigned_to == m.id)
        dist_lines.append(f"  {m.display_name}: {count} afgerond deze week, {open_count} open")
    if dist_lines:
        parts.append("TAAKVERDELING DEZE WEEK:\n" + "\n".join(dist_lines))

    if out_of_stock:
        parts.append("OP (voorraad = 0):\n" + "\n".join(
            f"  - {i.name} ({i.unit})" for i in out_of_stock
        ))

    if low_stock:
        low_lines = []
        for i in low_stock:
            if i.current_quantity <= 0:
                continue
            line = f"  - {i.name}: {i.current_quantity} {i.unit} (drempel: {i.threshold_quantity})"
            if i.average_consumption_rate and i.average_consumption_rate > 0:
                days_left = int(float(i.current_quantity) / float(i.average_consumption_rate))
                line += f" — verbruik ~{float(i.average_consumption_rate):.1f}/dag, nog ~{days_left} dagen"
            low_lines.append(line)
        if low_lines:
            parts.append("BIJNA OP:\n" + "\n".join(low_lines))

    if all_items:
        in_stock = [i for i in all_items if i.current_quantity > i.threshold_quantity]
        if in_stock:
            parts.append("VOORRAAD OK:\n" + "\n".join(
                f"  - {i.name}: {i.current_quantity} {i.unit}" for i in in_stock[:10]
            ))

    if upcoming_events:
        parts.append("AGENDA KOMENDE 48 UUR:\n" + "\n".join(
            f"  - {e.title}: {e.start_time.strftime('%a %d %b %H:%M')}"
            + (f" ({e.location})" if e.location else "")
            for e in upcoming_events
        ))

    if patterns:
        parts.append("GEDETECTEERDE PATRONEN:\n" + "\n".join(
            f"  - {p.description} (zekerheid: {p.confidence_score:.0%})" for p in patterns
        ))

    return "\n\n".join(parts)


@router.post("", response_model=ChatResponse)
@limiter.limit("20/minute")
async def send_chat_message(
    request: Request,
    payload: ChatRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and get AI response with full household context."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.household_id == member.household_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    recent = list(reversed(result.scalars().all()))

    messages = [{"role": msg.role, "content": msg.content} for msg in recent]
    messages.append({"role": "user", "content": payload.message})

    context = await _build_full_context(db, member.household_id, member)

    system_prompt = f"""Je bent de persoonlijke gezinsassistent van dit huishouden. Je bent proactief, denkt mee, en kent alle details.

BELANGRIJKE REGELS:
- Antwoord altijd in het Nederlands
- Wees direct, concreet en eerlijk — geen vage adviezen
- Je kent de volledige situatie: taken, voorraad, agenda, patronen
- Denk actief mee: als je ziet dat iets bijna op is, stel voor om het op de boodschappenlijst te zetten
- Als er morgen opvang is, herinner aan de luiertas, eten, wisselkleding
- Als taken scheef verdeeld zijn, benoem het eerlijk
- Geef korte, actionable antwoorden — niet langer dan nodig
- Gebruik de voorraaddata om slim mee te denken: als luiers 4 dagen meegaan en er zijn er nog 3, zeg dat
- Als je een actie voorstelt, formuleer het als een concreet voorstel dat de gebruiker kan bevestigen

HUIDIGE SITUATIE VAN DIT HUISHOUDEN:
{context}

Je praat nu met: {member.display_name} (rol: {member.role.value})
Datum/tijd: {datetime.now(timezone.utc).strftime('%A %d %B %Y, %H:%M')}"""

    try:
        reply = await call_claude(
            system=system_prompt,
            user_message=payload.message,
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=messages,
        )
    except AICallError as e:
        logger.error(f"Chat failed: {e}")
        reply = "Sorry, ik kan even niet antwoorden. Probeer het over een paar seconden opnieuw."

    user_msg = ChatMessage(
        household_id=member.household_id,
        member_id=member.id,
        role="user",
        content=payload.message,
    )
    assistant_msg = ChatMessage(
        household_id=member.household_id,
        member_id=member.id,
        role="assistant",
        content=reply,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        reply=reply,
        message_id=assistant_msg.id,
        created_at=assistant_msg.created_at,
    )


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_chat_history(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.household_id == member.household_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
    )
    return list(reversed(result.scalars().all()))
