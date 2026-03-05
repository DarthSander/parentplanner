import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.member import Member
from models.pattern import Pattern
from models.task import Task, TaskCompletion, TaskStatus
from schemas.ai_generated import AIGeneratedPattern
from services.ai.ai_utils import AICallError, call_claude, validate_json_list
from services.vector.retrieval import retrieve_context

logger = logging.getLogger(__name__)


async def analyze_patterns(db: AsyncSession, household_id: UUID):
    """Analyze task patterns for a household over the past 30 days."""
    since = datetime.now(timezone.utc) - timedelta(days=30)

    # Get completions
    completions_result = await db.execute(
        select(TaskCompletion).where(
            TaskCompletion.household_id == household_id,
            TaskCompletion.completed_at >= since,
        )
    )
    completions = completions_result.scalars().all()

    # Get overdue tasks
    overdue_result = await db.execute(
        select(Task).where(
            Task.household_id == household_id,
            Task.status.in_([TaskStatus.open, TaskStatus.snoozed]),
            Task.due_date < datetime.now(timezone.utc),
        )
    )
    overdue_tasks = overdue_result.scalars().all()

    # Get members
    members_result = await db.execute(
        select(Member).where(Member.household_id == household_id)
    )
    members = {m.id: m for m in members_result.scalars().all()}

    context_docs = await retrieve_context(
        db, household_id,
        "taakpatronen verdeling wie doet wat snel langzaam vermijdt",
        top_k=20,
    )

    # Build summaries
    completion_lines = []
    for c in completions:
        member = members.get(c.completed_by)
        name = member.display_name if member else "Onbekend"
        duration = f" ({c.duration_minutes} min)" if c.duration_minutes else ""
        completion_lines.append(f"- {name}: taak afgerond{duration}")

    overdue_lines = []
    for t in overdue_tasks:
        assigned = members.get(t.assigned_to)
        name = assigned.display_name if assigned else "Niet toegewezen"
        overdue_lines.append(f"- '{t.title}' ({t.category}), {name}, {t.snooze_count}x uitgesteld")

    system_prompt = """
Je analyseert gezinstaken en detecteert patronen. Geef een JSON array van patronen.
Elk patroon heeft:
- pattern_type: task_avoidance | task_affinity | inventory_rate | schedule_conflict | complementary_split
- member_id: UUID string of null voor huishoudelijke patronen
- description: Nederlandse beschrijving
- confidence_score: 0.0 tot 1.0
- metadata: object met extra context

Wees eerlijk en direct. Noem ook negatieve patronen.
Antwoord alleen met de JSON array.
"""

    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"""
AFGERONDE TAKEN AFGELOPEN 30 DAGEN ({len(completions)} totaal):
{chr(10).join(completion_lines[:30])}

VERLOPEN / UITGESTELDE TAKEN ({len(overdue_tasks)} totaal):
{chr(10).join(overdue_lines[:20])}

BESTAANDE CONTEXT:
{chr(10).join(context_docs[:10])}
""",
            max_tokens=2000,
        )
        patterns_data = validate_json_list(response, AIGeneratedPattern)
    except AICallError as e:
        logger.error(f"Failed to parse patterns for household {household_id}: {e}")
        return

    for pattern_item in patterns_data:
        # Check for existing similar pattern
        existing_result = await db.execute(
            select(Pattern).where(
                Pattern.household_id == household_id,
                Pattern.pattern_type == pattern_item.pattern_type,
                Pattern.member_id == pattern_item.member_id,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.last_confirmed_at = datetime.now(timezone.utc)
            existing.confidence_score = pattern_item.confidence_score
            existing.description = pattern_item.description
        else:
            pattern = Pattern(
                household_id=household_id,
                member_id=pattern_item.member_id,
                pattern_type=pattern_item.pattern_type,
                description=pattern_item.description,
                confidence_score=pattern_item.confidence_score,
                metadata_=pattern_item.metadata or {},
            )
            db.add(pattern)

    await db.commit()
