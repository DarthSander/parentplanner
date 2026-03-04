from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.security import get_current_user_id
from models.household import Household
from models.member import Member, MemberRole
from schemas.member import (
    InviteAcceptRequest,
    InviteValidateResponse,
    MemberInvite,
    MemberResponse,
    MemberUpdate,
)
from services.invite_service import accept_invite, create_invite, validate_invite_token

router = APIRouter()


@router.get("", response_model=list[MemberResponse])
async def list_members(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List all members of the current household."""
    result = await db.execute(
        select(Member).where(Member.household_id == member.household_id)
    )
    return result.scalars().all()


@router.post("/invite", response_model=dict, status_code=status.HTTP_201_CREATED)
async def invite_member(
    payload: MemberInvite,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Send a magic link invite to a new member. Only owners can invite."""
    if member.role != MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alleen de eigenaar kan leden uitnodigen.",
        )

    token = await create_invite(
        db=db,
        household_id=member.household_id,
        inviter_name=member.display_name,
        email=payload.email,
        role=payload.role.value,
        display_name=payload.display_name,
    )
    return {"message": "Uitnodiging verstuurd.", "token": token}


@router.post("/invite/accept", response_model=MemberResponse)
async def accept_invite_endpoint(
    payload: InviteAcceptRequest,
    user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Accept an invite using the magic link token."""
    try:
        new_member = await accept_invite(db, payload.token, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return new_member


@router.get("/invite/validate", response_model=InviteValidateResponse)
async def validate_invite_endpoint(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Validate an invite token without accepting it (for frontend preview)."""
    try:
        payload = validate_invite_token(token)
    except ValueError:
        return InviteValidateResponse(valid=False)

    # Get household name for preview
    result = await db.execute(
        select(Household).where(Household.id == payload["household_id"])
    )
    household = result.scalar_one_or_none()

    return InviteValidateResponse(
        valid=True,
        household_name=household.name if household else None,
        role=payload.get("role"),
        display_name=payload.get("display_name"),
        email=payload.get("email"),
    )


@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    current_member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Update a member. Owners can update anyone, others can only update themselves."""
    result = await db.execute(
        select(Member).where(
            Member.id == member_id,
            Member.household_id == current_member.household_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if current_member.role != MemberRole.owner and target.id != current_member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Je kunt alleen je eigen profiel aanpassen.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, field, value)

    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: UUID,
    current_member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the household. Only owners can remove others."""
    result = await db.execute(
        select(Member).where(
            Member.id == member_id,
            Member.household_id == current_member.household_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if target.role == MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="De eigenaar kan niet verwijderd worden.",
        )

    if current_member.role != MemberRole.owner and target.id != current_member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alleen de eigenaar kan andere leden verwijderen.",
        )

    await db.delete(target)
    await db.commit()
