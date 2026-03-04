from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from models.member import Member, MemberRole
from models.subscription import Subscription
from schemas.subscription import SubscriptionResponse

router = APIRouter()


@router.get("/me", response_model=SubscriptionResponse)
async def get_subscription(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(Subscription.household_id == member.household_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return sub


@router.post("/checkout")
async def create_checkout(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session."""
    if member.role != MemberRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Alleen de eigenaar kan het abonnement beheren.")

    # TODO: Implement Stripe checkout session creation (step 15)
    return {"message": "Stripe checkout wordt geïmplementeerd in stap 15."}


@router.post("/portal")
async def create_portal(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe customer portal session."""
    if member.role != MemberRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # TODO: Implement Stripe portal session creation (step 15)
    return {"message": "Stripe portal wordt geïmplementeerd in stap 15."}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role != MemberRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # TODO: Cancel via Stripe API (step 15)
    pass
