from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.rate_limiter import limiter
from models.member import Member
from models.pattern import Pattern
from schemas.pattern import PatternResponse

router = APIRouter()


@router.get("", response_model=list[PatternResponse])
async def list_patterns(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Pattern)
        .where(Pattern.household_id == member.household_id)
        .order_by(Pattern.last_confirmed_at.desc())
    )
    return result.scalars().all()


@router.post("/analyze-now", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/hour")
async def analyze_now(
    request: Request,
    member: Member = Depends(get_current_member),
):
    """Manually trigger pattern analysis (rate limited: 5/hour)."""
    # TODO: Trigger Celery task for pattern analysis (step 11)
    return {"message": "Patronenanalyse is gestart. Resultaten verschijnen binnen enkele minuten."}
