import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task, TaskCategory
from services.ai.ai_utils import AICallError, call_claude
from services.vector.retrieval import retrieve_context

logger = logging.getLogger(__name__)


async def generate_daycare_briefing(
    db: AsyncSession,
    household_id: UUID,
    daycare_name: str,
    date: datetime,
) -> str | None:
    """Generate a daycare briefing for a specific date."""
    context_docs = await retrieve_context(
        db, household_id,
        f"opvang briefing {date.strftime('%A')} bijzonderheden kind",
        top_k=10,
        source_types=["task", "inventory", "onboarding_answer", "pattern"],
    )

    # Get baby care tasks for today
    result = await db.execute(
        select(Task).where(
            Task.household_id == household_id,
            Task.category == TaskCategory.baby_care,
        )
    )
    today_tasks = result.scalars().all()
    task_lines = [f"- {t.title}" + (f": {t.description}" if t.description else "") for t in today_tasks[:10]]

    try:
        briefing_text = await call_claude(
            system="""
Je schrijft een korte, vriendelijke dagbriefing voor de opvang of oppas.
Alleen relevante informatie voor de zorgverlener. Geen huishoudelijke of privé informatie.
Maximaal 200 woorden. Duidelijke koptjes. Nederlands.
""",
            user_message=f"""
Datum: {date.strftime('%A %d %B %Y')}
Ontvanger: {daycare_name}

BABYTAKEN VANDAAG:
{chr(10).join(task_lines) if task_lines else "Geen specifieke taken"}

RELEVANTE CONTEXT:
{chr(10).join(context_docs[:6])}

Genereer de briefing.
""",
            max_tokens=400,
        )
        return briefing_text
    except AICallError as e:
        logger.error(f"Daycare briefing failed for household {household_id}: {e}")
        return None
