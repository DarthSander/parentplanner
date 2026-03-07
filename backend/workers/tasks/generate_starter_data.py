"""
Celery task: generate starter tasks, inventory, and patterns after onboarding.

Triggered by POST /onboarding after saving the onboarding answers.
Generates a personalized start set so the user doesn't start with an empty app.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_starter_data(self, household_id: str, onboarding_id: str):
    """Generate starter tasks, inventory, and patterns from onboarding answers."""
    try:
        asyncio.run(_generate(UUID(household_id), UUID(onboarding_id)))
    except Exception as exc:
        logger.error(f"Starter data generation failed for {household_id}: {exc}")
        self.retry(exc=exc)


async def _generate(household_id: UUID, onboarding_id: UUID):
    from sqlalchemy import select

    from core.database import get_db_context
    from models.inventory import InventoryItem
    from models.member import Member
    from models.onboarding import OnboardingAnswer
    from models.pattern import Pattern
    from models.task import Task
    from services.ai.ai_utils import AICallError, call_claude, parse_json_response
    from workers.tasks.embed_document import embed_document

    async with get_db_context() as db:
        # Load onboarding
        result = await db.execute(
            select(OnboardingAnswer).where(OnboardingAnswer.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            logger.error(f"Onboarding {onboarding_id} not found")
            return

        # Load members
        members_result = await db.execute(
            select(Member).where(Member.household_id == household_id)
        )
        members = members_result.scalars().all()
        owner = next((m for m in members if m.role.value == "owner"), members[0] if members else None)
        partner = next((m for m in members if m.role.value == "partner"), None)

        if not owner:
            logger.error(f"No owner found for household {household_id}")
            return

        now = datetime.now(timezone.utc)

        # ── 1. Generate starter tasks via AI ──────────────────────────
        tasks_created = await _generate_starter_tasks(
            db, onboarding, household_id, owner, partner, now
        )

        # ── 2. Generate starter inventory ─────────────────────────────
        items_created = await _generate_starter_inventory(
            db, onboarding, household_id
        )

        # ── 3. Generate initial patterns ──────────────────────────────
        patterns_created = await _generate_initial_patterns(
            db, onboarding, household_id, owner, partner
        )

        await db.commit()

        # Embed everything async
        for task in tasks_created:
            embed_document.delay(str(task.id), "task")
        for item in items_created:
            embed_document.delay(str(item.id), "inventory")

        logger.info(
            f"Starter data for {household_id}: "
            f"{len(tasks_created)} tasks, {len(items_created)} items, "
            f"{len(patterns_created)} patterns"
        )


async def _generate_starter_tasks(db, onboarding, household_id, owner, partner, now):
    """Generate personalized starter tasks based on onboarding answers."""
    from models.task import Task
    from services.ai.ai_utils import AICallError, call_claude, parse_json_response

    # Build context for AI
    context_parts = []
    if onboarding.child_age_weeks is not None:
        context_parts.append(f"Kind is {onboarding.child_age_weeks} weken oud")
    elif onboarding.expected_due_date:
        context_parts.append(f"Uitgerekende datum: {onboarding.expected_due_date}")

    context_parts.append(f"Situatie: {onboarding.situation}")
    context_parts.append(f"Werksituatie ouder 1: {onboarding.work_situation_owner}")
    if onboarding.work_situation_partner:
        context_parts.append(f"Werksituatie ouder 2: {onboarding.work_situation_partner}")
    if onboarding.daycare_days:
        context_parts.append(f"Opvangdagen: {', '.join(onboarding.daycare_days)}")
    if onboarding.has_caregiver:
        context_parts.append("Er is een oppas/caregiver")
    if onboarding.pain_points:
        context_parts.append(f"Pijnpunten: {', '.join(onboarding.pain_points)}")

    member_info = f"Ouder 1: {owner.display_name} (id: {owner.id})"
    if partner:
        member_info += f"\nOuder 2: {partner.display_name} (id: {partner.id})"

    system = f"""Je genereert starttaken voor een gezinsplanner-app.
Het gezin heeft net de onboarding ingevuld. Maak 10-18 relevante taken.

REGELS:
- Mix van babyzorg, huishouden, en persoonlijke taken
- Terugkerende taken met recurrence_rule (iCal RRULE)
- Verdeel eerlijk over beide ouders als er een partner is
- Pas taken aan op leeftijd kind (baby <12 wk = veel voedingstaken, >16 wk = vast voedsel, etc.)
- Als opvangdagen bekend zijn: maak inpaktaken voor de avond ervoor
- Als pijnpunt "boodschappen" is: maak wekelijkse boodschappentaak
- Als pijnpunt "slaaptekort" is: maak wisselschema nacht-taken
- due_date relatief: gebruik "today+N" formaat (bijv. "today+0", "today+1", "today+7")

Antwoord ALLEEN met JSON array:
[{{"title": "...", "description": "...", "category": "baby_care|household|work|private", "task_type": "quick|prep", "estimated_minutes": N, "assigned_to": "member-uuid|null", "due_offset_days": N, "recurrence_rule": "RRULE|null"}}]

GEZINSLEDEN:
{member_info}"""

    try:
        response = await call_claude(
            system=system,
            user_message=f"Gezinssituatie:\n{chr(10).join(context_parts)}",
            max_tokens=2500,
        )
        tasks_data = parse_json_response(response)
        if not isinstance(tasks_data, list):
            tasks_data = [tasks_data]
    except (AICallError, Exception) as e:
        logger.warning(f"AI task generation failed, using defaults: {e}")
        tasks_data = _default_starter_tasks(owner, partner, onboarding)

    created = []
    for item in tasks_data:
        try:
            due_offset = item.get("due_offset_days", 0)
            due_date = now + timedelta(days=due_offset) if due_offset is not None else None

            assigned_to = item.get("assigned_to")
            # Validate assigned_to is an actual member
            valid_ids = {str(owner.id)}
            if partner:
                valid_ids.add(str(partner.id))
            if assigned_to and str(assigned_to) not in valid_ids:
                assigned_to = None

            task = Task(
                household_id=household_id,
                title=str(item.get("title", "Taak"))[:200],
                description=item.get("description"),
                category=item.get("category", "household"),
                task_type=item.get("task_type", "quick"),
                estimated_minutes=item.get("estimated_minutes"),
                assigned_to=assigned_to,
                due_date=due_date,
                recurrence_rule=item.get("recurrence_rule"),
                ai_generated=True,
                created_by=owner.id,
            )
            db.add(task)
            created.append(task)
        except Exception as e:
            logger.warning(f"Skipping invalid starter task: {e}")
            continue

    await db.flush()
    return created


def _default_starter_tasks(owner, partner, onboarding):
    """Fallback tasks if AI generation fails."""
    owner_id = str(owner.id)
    partner_id = str(partner.id) if partner else None
    tasks = [
        {"title": "Luiers kopen", "category": "household", "task_type": "quick",
         "estimated_minutes": 30, "assigned_to": owner_id, "due_offset_days": 1},
        {"title": "Was draaien", "category": "household", "task_type": "quick",
         "estimated_minutes": 15, "assigned_to": partner_id, "due_offset_days": 0,
         "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO,TH"},
        {"title": "Flesjes klaarmaken", "category": "baby_care", "task_type": "quick",
         "estimated_minutes": 10, "assigned_to": owner_id, "due_offset_days": 0,
         "recurrence_rule": "FREQ=DAILY"},
        {"title": "Badtijd baby", "category": "baby_care", "task_type": "quick",
         "estimated_minutes": 20, "assigned_to": partner_id or owner_id, "due_offset_days": 0,
         "recurrence_rule": "FREQ=DAILY"},
        {"title": "Wekelijkse boodschappen", "category": "household", "task_type": "prep",
         "estimated_minutes": 60, "assigned_to": owner_id, "due_offset_days": 3,
         "recurrence_rule": "FREQ=WEEKLY;BYDAY=SA"},
        {"title": "Consultatieburo afspraak plannen", "category": "baby_care", "task_type": "prep",
         "estimated_minutes": 15, "assigned_to": owner_id, "due_offset_days": 7},
    ]

    if onboarding.daycare_days:
        tasks.append({
            "title": "Luiertas inpakken voor opvang", "category": "baby_care", "task_type": "prep",
            "estimated_minutes": 15, "assigned_to": partner_id or owner_id, "due_offset_days": 0,
            "description": "Luiers, wisselkleding, eten, slaapzakje, speentje",
        })

    if onboarding.pain_points and "sleep_deprivation" in onboarding.pain_points:
        tasks.append({
            "title": "Nachtvoeding (wissel)", "category": "baby_care", "task_type": "quick",
            "estimated_minutes": 30, "assigned_to": owner_id, "due_offset_days": 0,
            "recurrence_rule": "FREQ=DAILY", "description": "Wissel elke nacht af",
        })

    return tasks


async def _generate_starter_inventory(db, onboarding, household_id):
    """Generate starter inventory items based on child age and situation."""
    from models.inventory import InventoryItem

    items_data = [
        # Baby essentials
        {"name": "Luiers", "category": "baby", "current_quantity": 40, "unit": "stuks",
         "threshold_quantity": 10, "average_consumption_rate": 7},
        {"name": "Billendoekjes", "category": "baby", "current_quantity": 80, "unit": "stuks",
         "threshold_quantity": 20, "average_consumption_rate": 8},
        {"name": "Sudocrem / zinkzalf", "category": "baby", "current_quantity": 1, "unit": "tube",
         "threshold_quantity": 1},
    ]

    # Age-dependent items
    age = onboarding.child_age_weeks
    if age is not None:
        if age < 26:
            # Baby < 6 months — formula/milk focused
            items_data.extend([
                {"name": "Flesvoeding / melkpoeder", "category": "baby", "current_quantity": 2,
                 "unit": "pakken", "threshold_quantity": 1, "average_consumption_rate": 0.3},
                {"name": "Flesjes", "category": "baby", "current_quantity": 6, "unit": "stuks",
                 "threshold_quantity": 4},
                {"name": "Spenen", "category": "baby", "current_quantity": 4, "unit": "stuks",
                 "threshold_quantity": 2},
            ])
        if age >= 17:
            # Baby >= 4 months — introducing solids
            items_data.extend([
                {"name": "Fruitpotjes", "category": "baby", "current_quantity": 6, "unit": "stuks",
                 "threshold_quantity": 3, "average_consumption_rate": 1},
                {"name": "Groentepotjes", "category": "baby", "current_quantity": 6, "unit": "stuks",
                 "threshold_quantity": 3, "average_consumption_rate": 1},
                {"name": "Rijstebloem / pap", "category": "baby", "current_quantity": 2, "unit": "pakken",
                 "threshold_quantity": 1},
            ])
        if age >= 26:
            # 6+ months — more solids
            items_data.extend([
                {"name": "Knijpfruit", "category": "baby", "current_quantity": 4, "unit": "stuks",
                 "threshold_quantity": 2, "average_consumption_rate": 0.5},
            ])
    else:
        # Prenatal — stock up
        items_data.extend([
            {"name": "Flesvoeding / melkpoeder", "category": "baby", "current_quantity": 3,
             "unit": "pakken", "threshold_quantity": 1},
            {"name": "Flesjes", "category": "baby", "current_quantity": 6, "unit": "stuks",
             "threshold_quantity": 4},
        ])

    # Household basics
    items_data.extend([
        {"name": "Wasmiddel", "category": "schoonmaak", "current_quantity": 1, "unit": "fles",
         "threshold_quantity": 1},
        {"name": "Vuilniszakken", "category": "schoonmaak", "current_quantity": 1, "unit": "rol",
         "threshold_quantity": 1},
        {"name": "Keukenrol", "category": "schoonmaak", "current_quantity": 4, "unit": "rollen",
         "threshold_quantity": 2, "average_consumption_rate": 0.5},
    ])

    created = []
    for item_data in items_data:
        item = InventoryItem(
            household_id=household_id,
            name=item_data["name"],
            category=item_data.get("category"),
            current_quantity=item_data.get("current_quantity", 0),
            unit=item_data.get("unit", "stuks"),
            threshold_quantity=item_data.get("threshold_quantity", 1),
            average_consumption_rate=item_data.get("average_consumption_rate"),
        )
        db.add(item)
        created.append(item)

    await db.flush()
    return created


async def _generate_initial_patterns(db, onboarding, household_id, owner, partner):
    """Seed initial patterns based on work situation and family setup."""
    from models.pattern import Pattern

    created = []

    work_owner = onboarding.work_situation_owner
    work_partner = onboarding.work_situation_partner

    if partner and work_owner and work_partner:
        # Distribution pattern based on work situation
        if work_owner == "leave" and work_partner == "fulltime":
            desc = (
                f"{owner.display_name} is met verlof en zal overdag het merendeel van de "
                f"babytaken doen. {partner.display_name} werkt voltijd en neemt avond/weekend over."
            )
            p = Pattern(
                household_id=household_id, member_id=owner.id,
                pattern_type="complementary_split", description=desc,
                confidence_score=0.7, metadata={"source": "onboarding", "basis": "work_situation"},
            )
            db.add(p)
            created.append(p)

        elif work_owner == "fulltime" and work_partner == "leave":
            desc = (
                f"{partner.display_name} is met verlof en zal overdag het merendeel van de "
                f"babytaken doen. {owner.display_name} werkt voltijd en neemt avond/weekend over."
            )
            p = Pattern(
                household_id=household_id, member_id=partner.id,
                pattern_type="complementary_split", description=desc,
                confidence_score=0.7, metadata={"source": "onboarding", "basis": "work_situation"},
            )
            db.add(p)
            created.append(p)

        elif work_owner == "parttime" and work_partner == "parttime":
            desc = (
                f"Beide ouders werken deeltijd. Taakverdeling kan gelijk zijn — "
                f"de AI zal monitoren of dit in de praktijk ook zo is."
            )
            p = Pattern(
                household_id=household_id, member_id=None,
                pattern_type="complementary_split", description=desc,
                confidence_score=0.5, metadata={"source": "onboarding", "basis": "work_situation"},
            )
            db.add(p)
            created.append(p)

    if onboarding.pain_points:
        if "task_distribution" in onboarding.pain_points:
            p = Pattern(
                household_id=household_id, member_id=None,
                pattern_type="task_avoidance", description=(
                    "Taakverdeling is aangemerkt als pijnpunt bij intake. "
                    "De AI zal extra letten op eerlijke verdeling en onbalans signaleren."
                ),
                confidence_score=0.6,
                metadata={"source": "onboarding", "pain_point": "task_distribution"},
            )
            db.add(p)
            created.append(p)

        if "groceries" in onboarding.pain_points:
            p = Pattern(
                household_id=household_id, member_id=None,
                pattern_type="inventory_rate",
                description="Boodschappen vergeten is een pijnpunt. Voorraadwaarschuwingen extra agressief.",
                confidence_score=0.6,
                metadata={"source": "onboarding", "pain_point": "groceries"},
            )
            db.add(p)
            created.append(p)

        if "schedule" in onboarding.pain_points:
            p = Pattern(
                household_id=household_id, member_id=None,
                pattern_type="schedule_conflict",
                description="Agenda-chaos is een pijnpunt. Extra aandacht voor kalenderconflicten en planning.",
                confidence_score=0.6,
                metadata={"source": "onboarding", "pain_point": "schedule"},
            )
            db.add(p)
            created.append(p)

    await db.flush()
    return created
