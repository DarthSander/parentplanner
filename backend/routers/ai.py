from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.rate_limiter import limiter
from models.calendar import CalendarEvent
from models.inventory import InventoryItem
from models.member import Member
from models.pattern import Pattern
from models.task import Task, TaskCompletion, TaskStatus
from services.ai.ai_utils import AICallError, call_claude, parse_json_response

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class TaskSuggestRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class TaskSuggestResponse(BaseModel):
    category: str
    task_type: str
    estimated_minutes: int | None
    suggested_assignee_id: str | None
    reasoning: str


class TaskParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class TaskParseResponse(BaseModel):
    title: str
    category: str
    task_type: str
    estimated_minutes: int | None
    suggested_assignee_id: str | None
    due_date: str | None
    reasoning: str


class InsightItem(BaseModel):
    type: str  # balance | warning | pattern | praise
    message: str


class SuggestionAction(BaseModel):
    label: str
    action_type: str  # create_task | restock_item | open_chat | navigate
    payload: dict = {}


class ProactiveSuggestion(BaseModel):
    id: str
    icon: str
    message: str
    priority: int  # 1=urgent, 2=important, 3=nice-to-have
    context: str  # all, dashboard, inventory, tasks, calendar
    actions: list[SuggestionAction] = []


class DailyBriefResponse(BaseModel):
    greeting: str
    summary: str
    focus_items: list[dict]
    stats: dict


# ── Helpers ────────────────────────────────────────────────────────────────

async def _member_context(db: AsyncSession, household_id: UUID) -> tuple[list[Member], str]:
    result = await db.execute(
        select(Member).where(Member.household_id == household_id)
    )
    members = result.scalars().all()
    lines = "\n".join(
        f"- {m.display_name} (id: {m.id}, rol: {m.role.value})"
        for m in members if m.role.value != "daycare"
    )
    return members, lines


# ── Proactive Suggestions (data-driven, no AI call for speed) ─────────────

@router.get("/suggestions", response_model=list[ProactiveSuggestion])
@limiter.limit("15/minute")
async def get_proactive_suggestions(
    request: Request,
    page: str = "all",
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Smart proactive suggestions based on current household state."""
    now = datetime.now(timezone.utc)
    suggestions: list[ProactiveSuggestion] = []
    suggestion_id = 0

    def _id():
        nonlocal suggestion_id
        suggestion_id += 1
        return f"sug-{suggestion_id}"

    # --- Voorraad ---
    inventory_result = await db.execute(
        select(InventoryItem).where(InventoryItem.household_id == member.household_id)
    )
    all_items = inventory_result.scalars().all()

    out_of_stock = [i for i in all_items if i.current_quantity == 0]
    almost_out = [i for i in all_items if 0 < i.current_quantity <= i.threshold_quantity]
    running_low_soon = [
        i for i in all_items
        if i.average_consumption_rate and float(i.average_consumption_rate) > 0
        and i.current_quantity > i.threshold_quantity
        and (float(i.current_quantity) / float(i.average_consumption_rate)) <= 3
    ]

    if out_of_stock:
        names = ", ".join(i.name for i in out_of_stock[:3])
        extra = f" en {len(out_of_stock) - 3} meer" if len(out_of_stock) > 3 else ""
        suggestions.append(ProactiveSuggestion(
            id=_id(), icon="alert", priority=1, context="all",
            message=f"{names}{extra} is op. Toevoegen aan boodschappenlijst?",
            actions=[
                SuggestionAction(label="Boodschappenlijst", action_type="navigate", payload={"path": "/inventory"}),
                SuggestionAction(label="Taak aanmaken", action_type="create_task", payload={
                    "title": f"Boodschappen: {names}", "category": "household"
                }),
            ],
        ))

    for item in almost_out[:2]:
        days_text = ""
        if item.average_consumption_rate and float(item.average_consumption_rate) > 0:
            days_left = int(float(item.current_quantity) / float(item.average_consumption_rate))
            days_text = f" (nog ~{days_left} dagen)"
        suggestions.append(ProactiveSuggestion(
            id=_id(), icon="inventory", priority=2, context="all",
            message=f"{item.name} is bijna op: {item.current_quantity} {item.unit}{days_text}",
            actions=[
                SuggestionAction(label="Bijvullen", action_type="restock_item", payload={"item_id": str(item.id)}),
                SuggestionAction(label="Op boodschappenlijst", action_type="create_task", payload={
                    "title": f"{item.name} kopen", "category": "household"
                }),
            ],
        ))

    for item in running_low_soon[:2]:
        days_left = int(float(item.current_quantity) / float(item.average_consumption_rate))
        suggestions.append(ProactiveSuggestion(
            id=_id(), icon="clock", priority=3, context="dashboard",
            message=f"{item.name} is over ~{days_left} dagen op",
            actions=[
                SuggestionAction(label="Op boodschappenlijst", action_type="create_task", payload={
                    "title": f"{item.name} kopen", "category": "household"
                }),
            ],
        ))

    # --- Agenda: morgen opvang? ---
    tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    events_result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.household_id == member.household_id,
            CalendarEvent.start_time >= tomorrow_start,
            CalendarEvent.start_time < tomorrow_end,
        )
        .order_by(CalendarEvent.start_time)
    )
    tomorrow_events = events_result.scalars().all()

    DAYCARE_KEYWORDS = ["opvang", "dagopvang", "kinderopvang", "creche", "bso"]
    for event in tomorrow_events:
        if any(kw in event.title.lower() for kw in DAYCARE_KEYWORDS):
            suggestions.append(ProactiveSuggestion(
                id=_id(), icon="bag", priority=1, context="all",
                message="Morgen opvang! Is de luiertas compleet? (luiers, wisselkleding, eten, slaapzak)",
                actions=[
                    SuggestionAction(label="Checklist maken", action_type="create_task", payload={
                        "title": "Luiertas inpakken voor opvang", "category": "baby_care", "task_type": "prep",
                    }),
                    SuggestionAction(label="Chat hierover", action_type="open_chat", payload={
                        "message": "Morgen is er opvang. Wat moet ik allemaal regelen?"
                    }),
                ],
            ))
            break

    # --- Taken ---
    overdue_count = await db.scalar(
        select(func.count()).select_from(Task).where(
            Task.household_id == member.household_id,
            Task.status.in_(["open", "snoozed"]),
            Task.due_date < now,
        )
    ) or 0

    if overdue_count >= 3:
        suggestions.append(ProactiveSuggestion(
            id=_id(), icon="warning", priority=1, context="all",
            message=f"Je hebt {overdue_count} verlopen taken. Wil je ze doorlopen?",
            actions=[
                SuggestionAction(label="Bekijk taken", action_type="navigate", payload={"path": "/tasks"}),
                SuggestionAction(label="Help me prioriteren", action_type="open_chat", payload={
                    "message": "Ik heb verlopen taken. Kun je me helpen prioriteren?"
                }),
            ],
        ))

    # Chronisch uitgesteld
    snoozed_result = await db.execute(
        select(Task)
        .where(
            Task.household_id == member.household_id,
            Task.status == "snoozed",
            Task.snooze_count >= 3,
        )
        .limit(2)
    )
    chronic_snoozed = snoozed_result.scalars().all()

    for task in chronic_snoozed[:1]:
        suggestions.append(ProactiveSuggestion(
            id=_id(), icon="snooze", priority=2, context="tasks",
            message=f"'{task.title}' is al {task.snooze_count}x uitgesteld. Herverdelen of schrappen?",
            actions=[
                SuggestionAction(label="Herverdelen", action_type="open_chat", payload={
                    "message": f"'{task.title}' is {task.snooze_count}x uitgesteld. Wie kan dit oppakken?"
                }),
                SuggestionAction(label="Bekijk", action_type="navigate", payload={"path": f"/tasks/{task.id}"}),
            ],
        ))

    # Niet-toegewezen taken
    unassigned_count = await db.scalar(
        select(func.count()).select_from(Task).where(
            Task.household_id == member.household_id,
            Task.status.in_(["open", "in_progress"]),
            Task.assigned_to.is_(None),
        )
    ) or 0

    if unassigned_count >= 3:
        suggestions.append(ProactiveSuggestion(
            id=_id(), icon="assign", priority=2, context="tasks",
            message=f"{unassigned_count} taken niet toegewezen. AI laten verdelen?",
            actions=[
                SuggestionAction(label="AI verdelen", action_type="open_chat", payload={
                    "message": "Kun je de niet-toegewezen taken eerlijk verdelen?"
                }),
                SuggestionAction(label="Zelf doen", action_type="navigate", payload={"path": "/tasks"}),
            ],
        ))

    # Filter en sorteer
    if page != "all":
        suggestions = [s for s in suggestions if s.context in ("all", page)]
    suggestions.sort(key=lambda s: s.priority)

    return suggestions[:6]


# ── Daily Brief ───────────────────────────────────────────────────────────

@router.get("/daily-brief", response_model=DailyBriefResponse)
@limiter.limit("10/minute")
async def get_daily_brief(
    request: Request,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized daily briefing for the dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_ago = now - timedelta(days=7)

    first_name = member.display_name.split()[0] if member.display_name else ""

    # Today's tasks
    today_tasks_result = await db.execute(
        select(Task).where(
            Task.household_id == member.household_id,
            Task.status.in_(["open", "in_progress"]),
            Task.due_date >= today_start, Task.due_date < today_end,
        ).order_by(Task.due_date)
    )
    today_tasks = today_tasks_result.scalars().all()

    # My open tasks
    my_tasks_result = await db.execute(
        select(Task).where(
            Task.household_id == member.household_id,
            Task.assigned_to == member.id,
            Task.status.in_(["open", "in_progress"]),
        )
    )
    my_tasks = my_tasks_result.scalars().all()

    # Overdue
    overdue_count = await db.scalar(
        select(func.count()).select_from(Task).where(
            Task.household_id == member.household_id,
            Task.status.in_(["open", "snoozed"]),
            Task.due_date < now,
        )
    ) or 0

    # Today's events
    events_result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.household_id == member.household_id,
            CalendarEvent.start_time >= today_start, CalendarEvent.start_time < today_end,
        ).order_by(CalendarEvent.start_time)
    )
    today_events = events_result.scalars().all()

    # Low stock
    low_stock_count = await db.scalar(
        select(func.count()).select_from(InventoryItem).where(
            InventoryItem.household_id == member.household_id,
            InventoryItem.current_quantity <= InventoryItem.threshold_quantity,
        )
    ) or 0

    # My completions this week
    my_completions = await db.scalar(
        select(func.count()).select_from(TaskCompletion).where(
            TaskCompletion.completed_by == member.id,
            TaskCompletion.completed_at >= week_ago,
        )
    ) or 0

    # Build focus items (max 5, prioritized)
    focus_items = []

    if overdue_count > 0:
        focus_items.append({
            "type": "overdue", "icon": "alert-circle",
            "label": f"{overdue_count} verlopen {'taak' if overdue_count == 1 else 'taken'}",
            "action": "/tasks", "urgent": True,
        })

    if low_stock_count > 0:
        focus_items.append({
            "type": "low_stock", "icon": "package",
            "label": f"{low_stock_count} {'item' if low_stock_count == 1 else 'items'} bijna op",
            "action": "/inventory", "urgent": low_stock_count >= 3,
        })

    for event in today_events[:2]:
        focus_items.append({
            "type": "event", "icon": "calendar",
            "label": f"{event.start_time.strftime('%H:%M')} {event.title}",
            "action": "/calendar", "urgent": False,
        })

    for task in today_tasks[:2]:
        focus_items.append({
            "type": "task", "icon": "check-circle",
            "label": task.title,
            "action": f"/tasks/{task.id}", "urgent": False,
        })

    # Greeting
    hour = now.hour
    if hour < 12:
        time_greeting = "Goedemorgen"
    elif hour < 18:
        time_greeting = "Goedemiddag"
    else:
        time_greeting = "Goedenavond"
    greeting = f"{time_greeting}, {first_name}"

    # Summary
    summary_parts = []
    if len(today_tasks) > 0:
        summary_parts.append(f"{len(today_tasks)} taken vandaag")
    if len(today_events) > 0:
        summary_parts.append(f"{len(today_events)} afspraken")
    if overdue_count > 0:
        summary_parts.append(f"{overdue_count} verlopen")
    if low_stock_count > 0:
        summary_parts.append(f"{low_stock_count} voorraad laag")

    summary = "Je hebt " + ", ".join(summary_parts) + "." if summary_parts else "Alles ziet er rustig uit vandaag."

    return DailyBriefResponse(
        greeting=greeting,
        summary=summary,
        focus_items=focus_items[:5],
        stats={
            "tasks_today": len(today_tasks),
            "my_open": len(my_tasks),
            "overdue": overdue_count,
            "events_today": len(today_events),
            "low_stock": low_stock_count,
            "completed_this_week": my_completions,
        },
    )


# ── Existing endpoints ────────────────────────────────────────────────────

@router.post("/suggest-task", response_model=TaskSuggestResponse)
@limiter.limit("30/minute")
async def suggest_task(
    request: Request,
    payload: TaskSuggestRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Given a task title, return AI suggestions."""
    recent_result = await db.execute(
        select(Task).where(Task.household_id == member.household_id)
        .order_by(Task.created_at.desc()).limit(40)
    )
    recent_tasks = recent_result.scalars().all()
    task_lines = "\n".join(
        f"- {t.title} | {t.category.value} | {t.task_type.value} | {t.estimated_minutes or '?'} min"
        for t in recent_tasks[:20]
    )
    _, member_lines = await _member_context(db, member.household_id)

    system = """Je bent een intelligente taakassistent voor een gezinsplanner.
Op basis van een taaknaam geef je een JSON suggestie terug.

Categorieën: baby_care, household, work, private
Types: quick (< 30 min), prep (30+ min of multi-stap)

Antwoord ALLEEN met geldige JSON:
{"category": "...", "task_type": "...", "estimated_minutes": 15, "suggested_assignee_id": "uuid-or-null", "reasoning": "Eén zin"}"""

    try:
        response = await call_claude(system=system, user_message=f'Taak: "{payload.title}"\nGezin:\n{member_lines}\nEerdere taken:\n{task_lines or "Geen"}', max_tokens=300)
        data = parse_json_response(response)
        return TaskSuggestResponse(
            category=data.get("category", "household"), task_type=data.get("task_type", "quick"),
            estimated_minutes=data.get("estimated_minutes"), suggested_assignee_id=data.get("suggested_assignee_id"),
            reasoning=data.get("reasoning", ""),
        )
    except (AICallError, Exception):
        return TaskSuggestResponse(category="household", task_type="quick", estimated_minutes=None, suggested_assignee_id=None, reasoning="")


@router.post("/parse-task", response_model=TaskParseResponse)
@limiter.limit("20/minute")
async def parse_task(
    request: Request,
    payload: TaskParseRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Parse free-text into a structured task."""
    _, member_lines = await _member_context(db, member.household_id)
    today = datetime.now(timezone.utc).date().isoformat()

    system = f"""Je bent een taakparser voor een gezinsplanner. Vandaag is {today}.
Zet vrije tekst om naar een gestructureerde taak.

Regels:
- Beknopte titel (max 60 tekens)
- Detecteer deadlines: 'morgen', 'woensdag', 'volgende week'
- Wijs toe als een naam overeenkomt met een gezinslid
- Categoriseer: baby_care / household / work / private

Antwoord ALLEEN met JSON:
{{"title": "...", "category": "...", "task_type": "...", "estimated_minutes": null, "suggested_assignee_id": "uuid-or-null", "due_date": "ISO or null", "reasoning": "..."}}

Gezinsleden:
{member_lines}"""

    try:
        response = await call_claude(system=system, user_message=f'Parseer: "{payload.text}"', max_tokens=400)
        data = parse_json_response(response)
        return TaskParseResponse(
            title=data.get("title", payload.text[:60]), category=data.get("category", "household"),
            task_type=data.get("task_type", "quick"), estimated_minutes=data.get("estimated_minutes"),
            suggested_assignee_id=data.get("suggested_assignee_id"), due_date=data.get("due_date"),
            reasoning=data.get("reasoning", ""),
        )
    except (AICallError, Exception):
        return TaskParseResponse(
            title=payload.text[:60], category="household", task_type="quick",
            estimated_minutes=None, suggested_assignee_id=None, due_date=None, reasoning="",
        )


@router.get("/insights", response_model=list[InsightItem])
@limiter.limit("10/minute")
async def get_insights(
    request: Request,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Generate 2-4 personalized AI insights."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    members, _ = await _member_context(db, member.household_id)

    dist_lines = []
    for m in members:
        if m.role.value == "daycare":
            continue
        completed = await db.scalar(
            select(func.count()).select_from(TaskCompletion)
            .where(TaskCompletion.completed_by == m.id, TaskCompletion.completed_at >= since)
        ) or 0
        open_count = await db.scalar(
            select(func.count()).select_from(Task)
            .where(Task.assigned_to == m.id, Task.household_id == member.household_id, Task.status.in_(["open", "in_progress"]))
        ) or 0
        dist_lines.append(f"- {m.display_name}: {completed} afgerond, {open_count} open")

    overdue_result = await db.execute(
        select(Task).where(Task.household_id == member.household_id, Task.status.in_(["open", "snoozed"]))
        .order_by(Task.snooze_count.desc()).limit(5)
    )
    overdue = overdue_result.scalars().all()
    overdue_lines = [f"- '{t.title}' ({t.snooze_count}x uitgesteld)" for t in overdue if t.snooze_count > 0 or (t.due_date and t.due_date < datetime.now(timezone.utc))]

    patterns_result = await db.execute(
        select(Pattern).where(Pattern.household_id == member.household_id).order_by(Pattern.last_confirmed_at.desc()).limit(3)
    )
    pattern_lines = [f"- {p.description}" for p in patterns_result.scalars().all()]

    system = """Gezinsassistent: korte observaties over taakverdeling. Eerlijk. Max 4. Eén zin per insight.
Types: balance, warning, pattern, praise
JSON array: [{"type": "...", "message": "..."}]"""

    try:
        response = await call_claude(system=system, user_message=f"Verdeling:\n{chr(10).join(dist_lines) or 'Geen'}\nUitgesteld:\n{chr(10).join(overdue_lines) or 'Geen'}\nPatronen:\n{chr(10).join(pattern_lines) or 'Geen'}\nVoor: {member.display_name}", max_tokens=500)
        data = parse_json_response(response)
        if not isinstance(data, list):
            data = [data]
        return [InsightItem(type=item.get("type", "pattern"), message=item.get("message", "")) for item in data if item.get("message")]
    except (AICallError, Exception):
        return []
