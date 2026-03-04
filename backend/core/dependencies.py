from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user_id
from models.member import Member


async def get_current_member(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Get the Member record for the authenticated user.
    A user must be a member of at least one household to use the app.
    """
    result = await db.execute(
        select(Member).where(Member.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Je bent nog geen lid van een huishouden.",
        )
    return member


async def require_role(*roles: str):
    """Factory for a dependency that checks if the current member has one of the allowed roles."""

    async def _check(member: Member = Depends(get_current_member)) -> Member:
        if member.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Deze actie vereist een van de volgende rollen: {', '.join(roles)}.",
            )
        return member

    return _check


def require_owner():
    """Dependency that requires the current member to be an owner."""

    async def _check(member: Member = Depends(get_current_member)) -> Member:
        if member.role.value != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Alleen de eigenaar kan deze actie uitvoeren.",
            )
        return member

    return _check
