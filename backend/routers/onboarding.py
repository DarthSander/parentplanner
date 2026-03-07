import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from models.member import Member
from models.onboarding import OnboardingAnswer
from schemas.onboarding import OnboardingCreate, OnboardingResponse
from services.ai.ai_utils import AICallError, call_claude

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def create_onboarding(
    payload: OnboardingCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Submit onboarding answers and generate AI start situation."""
    # Check if already completed
    existing = await db.execute(
        select(OnboardingAnswer).where(
            OnboardingAnswer.household_id == member.household_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Onboarding is al ingevuld voor dit huishouden.",
        )

    # Build onboarding record
    answer = OnboardingAnswer(
        household_id=member.household_id,
        child_age_weeks=payload.child_age_weeks,
        expected_due_date=payload.expected_due_date,
        situation=payload.situation.value,
        work_situation_owner=payload.work_situation_owner.value,
        work_situation_partner=payload.work_situation_partner.value if payload.work_situation_partner else None,
        daycare_days=payload.daycare_days,
        has_caregiver=payload.has_caregiver,
        pain_points=[p.value for p in payload.pain_points] if payload.pain_points else None,
    )

    # Generate AI summary
    try:
        summary = await _generate_onboarding_summary(payload)
        answer.ai_generated_summary = summary
    except AICallError as e:
        logger.error(f"Onboarding AI summary failed: {e}")
        # Continue without summary — graceful degradation

    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    # Generate starter tasks, inventory, and patterns asynchronously
    from workers.tasks.generate_starter_data import generate_starter_data
    generate_starter_data.delay(str(answer.household_id), str(answer.id))

    return answer


@router.get("", response_model=OnboardingResponse | None)
async def get_onboarding(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get onboarding answers for the current household."""
    result = await db.execute(
        select(OnboardingAnswer).where(
            OnboardingAnswer.household_id == member.household_id
        )
    )
    return result.scalar_one_or_none()


async def _generate_onboarding_summary(payload: OnboardingCreate) -> str:
    """Generate an AI summary of the onboarding intake."""
    situation_labels = {
        "couple": "koppel",
        "single": "alleenstaand",
        "co_parent": "co-ouderschap",
    }
    work_labels = {
        "fulltime": "voltijd",
        "parttime": "deeltijd",
        "leave": "verlof",
        "none": "niet werkzaam",
    }
    pain_labels = {
        "sleep_deprivation": "slaaptekort",
        "task_distribution": "taakverdeling",
        "groceries": "boodschappen vergeten",
        "schedule": "agenda-chaos",
        "finances": "financiën",
    }

    parts = [f"Gezinssituatie: {situation_labels.get(payload.situation.value, payload.situation.value)}"]

    if payload.child_age_weeks is not None:
        parts.append(f"Kind: {payload.child_age_weeks} weken oud")
    elif payload.expected_due_date:
        parts.append(f"Uitgerekende datum: {payload.expected_due_date}")

    parts.append(f"Werksituatie ouder 1: {work_labels.get(payload.work_situation_owner.value, '')}")
    if payload.work_situation_partner:
        parts.append(f"Werksituatie ouder 2: {work_labels.get(payload.work_situation_partner.value, '')}")

    if payload.daycare_days:
        parts.append(f"Opvangdagen: {', '.join(payload.daycare_days)}")

    if payload.has_caregiver:
        parts.append("Er is een externe zorgverlener betrokken")

    if payload.pain_points:
        labels = [pain_labels.get(p.value, p.value) for p in payload.pain_points]
        parts.append(f"Pijnpunten: {', '.join(labels)}")

    intake = ". ".join(parts)

    summary = await call_claude(
        system="Je vat een intake van een gezinsplanner-app samen in maximaal 150 woorden. "
               "Wees beknopt en feitelijk. Nederlands.",
        user_message=f"Vat deze intake samen:\n{intake}",
        max_tokens=300,
    )
    return summary
