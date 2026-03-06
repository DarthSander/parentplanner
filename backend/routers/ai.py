from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.rate_limiter import limiter
from models.member import Member
from models.pattern import Pattern
from models.task import Task, TaskCompletion, TaskStatus
from services.ai.ai_utils import AICallError, call_claude, parse_json_response

router = APIRouter()


# ── Request / Response schemas ─────────────────────────────────────────────

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
    type: str   # balance | warning | pattern | praise
    message: str


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


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/suggest-task", response_model=TaskSuggestResponse)
@limiter.limit("30/minute")
async def suggest_task(
    request: Request,
    payload: TaskSuggestRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Given a task title, return AI suggestions for category, type,
    estimated duration and best assignee — based on this household's history.
    """
    # Recent tasks for pattern context
    recent_result = await db.execute(
        select(Task)
        .where(Task.household_id == member.household_id)
        .order_by(Task.created_at.desc())
        .limit(40)
    )
    recent_tasks = recent_result.scalars().all()
    task_lines = "\n".join(
        f"- {t.title} | {t.category.value} | {t.task_type.value} | {t.estimated_minutes or '?'} min"
        for t in recent_tasks[:20]
    )

    _, member_lines = await _member_context(db, member.household_id)

    system = """Je bent een intelligente taakassistent voor een gezinsplanner.
Op basis van een taaknaam geef je een JSON suggestie terug.

Categorieën:
- baby_care: luiers, voeding, bad, slaap, arts, consultatieburo, speelgoed, opvangtas
- household: koken, schoonmaken, boodschappen, tuin, was, strijken, opruimen
- work: werk gerelateerd, vergadering, deadline
- private: persoonlijk, sport, hobby, dokter voor jezelf

Types:
- quick: direct uitvoerbaar, < 30 min
- prep: voorbereiding of planning, 30+ min of multi-stap

Antwoord ALLEEN met geldige JSON, geen andere tekst:
{
  "category": "...",
  "task_type": "...",
  "estimated_minutes": 15,
  "suggested_assignee_id": "uuid-or-null",
  "reasoning": "Één zin waarom"
}"""

    user_msg = f"""Nieuwe taaknaam: "{payload.title}"

Eerdere taken van dit gezin (voor patroonherkenning):
{task_lines or "Geen eerdere taken"}

Gezinsleden:
{member_lines}

Geef een suggestie voor deze taak."""

    try:
        response = await call_claude(system=system, user_message=user_msg, max_tokens=300)
        data = parse_json_response(response)
        return TaskSuggestResponse(
            category=data.get("category", "household"),
            task_type=data.get("task_type", "quick"),
            estimated_minutes=data.get("estimated_minutes"),
            suggested_assignee_id=data.get("suggested_assignee_id"),
            reasoning=data.get("reasoning", ""),
        )
    except (AICallError, Exception):
        return TaskSuggestResponse(
            category="household",
            task_type="quick",
            estimated_minutes=None,
            suggested_assignee_id=None,
            reasoning="",
        )


@router.post("/parse-task", response_model=TaskParseResponse)
@limiter.limit("20/minute")
async def parse_task(
    request: Request,
    payload: TaskParseRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Parse a free-text natural language string into a structured task.
    Supports things like 'luiers kopen voor woensdag toewijzen aan Jan'.
    """
    _, member_lines = await _member_context(db, member.household_id)
    today = datetime.now(timezone.utc).date().isoformat()

    system = f"""Je bent een taakparser voor een gezinsplanner. Vandaag is {today}.
Zet vrije tekst om naar een gestructureerde taak.

Regels:
- Haal de kern van de taak als beknopte titel op
- Detecteer deadline-hints: 'morgen', 'woensdag', 'volgende week', etc.
- Wijs toe als een naam in de tekst voorkomt die overeenkomt met een gezinslid
- Categoriseer logisch (baby_care / household / work / private)

Antwoord ALLEEN met geldige JSON:
{{
  "title": "Beknopte taaknaam (max 60 tekens)",
  "category": "...",
  "task_type": "...",
  "estimated_minutes": null,
  "suggested_assignee_id": "uuid-or-null",
  "due_date": "ISO 8601 datetime string or null",
  "reasoning": "Wat je herkend hebt"
}}

Gezinsleden:
{member_lines}"""

    try:
        response = await call_claude(
            system=system,
            user_message=f'Parseer: "{payload.text}"',
            max_tokens=400,
        )
        data = parse_json_response(response)
        return TaskParseResponse(
            title=data.get("title", payload.text[:60]),
            category=data.get("category", "household"),
            task_type=data.get("task_type", "quick"),
            estimated_minutes=data.get("estimated_minutes"),
            suggested_assignee_id=data.get("suggested_assignee_id"),
            due_date=data.get("due_date"),
            reasoning=data.get("reasoning", ""),
        )
    except (AICallError, Exception):
        return TaskParseResponse(
            title=payload.text[:60],
            category="household",
            task_type="quick",
            estimated_minutes=None,
            suggested_assignee_id=None,
            due_date=None,
            reasoning="",
        )


@router.get("/insights", response_model=list[InsightItem])
@limiter.limit("10/minute")
async def get_insights(
    request: Request,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate 2-4 personalised AI insights about task distribution,
    overdue items and detected patterns for this household.
    """
    since = datetime.now(timezone.utc) - timedelta(days=7)

    members, _ = await _member_context(db, member.household_id)

    dist_lines = []
    for m in members:
        if m.role.value == "daycare":
            continue
        completed = await db.scalar(
            select(func.count())
            .select_from(TaskCompletion)
            .where(
                TaskCompletion.completed_by == m.id,
                TaskCompletion.completed_at >= since,
            )
        ) or 0
        open_count = await db.scalar(
            select(func.count())
            .select_from(Task)
            .where(
                Task.assigned_to == m.id,
                Task.household_id == member.household_id,
                Task.status.in_(["open", "in_progress"]),
            )
        ) or 0
        dist_lines.append(f"- {m.display_name}: {completed} afgerond deze week, {open_count} open")

    # Top overdue / snoozed tasks
    overdue_result = await db.execute(
        select(Task)
        .where(
            Task.household_id == member.household_id,
            Task.status.in_(["open", "snoozed"]),
        )
        .order_by(Task.snooze_count.desc(), Task.due_date.asc().nullslast())
        .limit(5)
    )
    overdue = overdue_result.scalars().all()
    overdue_lines = [
        f"- '{t.title}' ({t.snooze_count}x uitgesteld)"
        for t in overdue if t.snooze_count > 0 or (t.due_date and t.due_date < datetime.now(timezone.utc))
    ]

    # Known patterns
    patterns_result = await db.execute(
        select(Pattern)
        .where(Pattern.household_id == member.household_id)
        .order_by(Pattern.last_confirmed_at.desc())
        .limit(3)
    )
    patterns = patterns_result.scalars().all()
    pattern_lines = [f"- {p.description}" for p in patterns]

    system = """Je bent een gezinsassistent die korte, directe observaties geeft over taakverdeling.
Wees eerlijk, ook over ongelijke verdeling. Spreek de gebruiker aan als 'jij' of bij naam.
Maximaal 4 inzichten. Elke insight is één Nederlandse zin, direct en concreet.

Type-keuze:
- balance: over taakverdeling tussen gezinsleden
- warning: over uitgestelde of vergeten taken
- pattern: over een gedetecteerd patroon
- praise: positieve observatie, alleen als er echt iets positiefs is

Antwoord ALLEEN met een JSON array:
[
  {"type": "balance", "message": "..."},
  {"type": "warning", "message": "..."}
]"""

    user_msg = f"""TAAKVERDELING AFGELOPEN 7 DAGEN:
{chr(10).join(dist_lines) or "Nog geen taakverdeling data"}

UITGESTELDE / VERLOPEN TAKEN:
{chr(10).join(overdue_lines) or "Geen uitgestelde taken"}

BEKENDE PATRONEN:
{chr(10).join(pattern_lines) or "Nog geen patronen"}

Genereer inzichten voor {member.display_name}."""

    try:
        response = await call_claude(system=system, user_message=user_msg, max_tokens=500)
        data = parse_json_response(response)
        if not isinstance(data, list):
            data = [data]
        return [
            InsightItem(type=item.get("type", "pattern"), message=item.get("message", ""))
            for item in data
            if item.get("message")
        ]
    except (AICallError, Exception):
        return []
