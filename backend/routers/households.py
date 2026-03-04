from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.security import get_current_user_id
from models.household import Household
from models.member import Member, MemberRole
from schemas.household import HouseholdCreate, HouseholdResponse, HouseholdUpdate

router = APIRouter()


@router.post("", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
async def create_household(
    payload: HouseholdCreate,
    user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new household. The creator becomes the owner."""
    household = Household(name=payload.name)
    db.add(household)
    await db.flush()

    owner = Member(
        household_id=household.id,
        user_id=user_id,
        role=MemberRole.owner,
        display_name=payload.name,  # will be updated during onboarding
    )
    db.add(owner)
    await db.commit()
    await db.refresh(household)
    return household


@router.get("/me", response_model=HouseholdResponse)
async def get_my_household(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's household."""
    result = await db.execute(
        select(Household).where(Household.id == member.household_id)
    )
    household = result.scalar_one_or_none()
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return household


@router.patch("/me", response_model=HouseholdResponse)
async def update_my_household(
    payload: HouseholdUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's household. Only owners can update."""
    if member.role != MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alleen de eigenaar kan het huishouden aanpassen.",
        )

    result = await db.execute(
        select(Household).where(Household.id == member.household_id)
    )
    household = result.scalar_one_or_none()
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(household, field, value)

    await db.commit()
    await db.refresh(household)
    return household
