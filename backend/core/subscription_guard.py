from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member

TIER_FEATURES = {
    "free": {
        "max_members": 2,
        "ai_analysis": False,
        "calendar_integration": False,
        "push_notifications": False,
        "patterns": False,
        "vector_memory": False,
        "inventory_auto_deduct": False,
        "caregiver_role": False,
        "daycare_briefing": False,
        "whatsapp_briefing": False,
        "partner_escalation": False,
        "smartthings": False,
    },
    "standard": {
        "max_members": 4,
        "ai_analysis": True,
        "calendar_integration": True,
        "push_notifications": True,
        "patterns": True,
        "vector_memory": True,
        "inventory_auto_deduct": False,
        "caregiver_role": False,
        "daycare_briefing": False,
        "whatsapp_briefing": False,
        "partner_escalation": False,
        "smartthings": False,
    },
    "family": {
        "max_members": None,
        "ai_analysis": True,
        "calendar_integration": True,
        "push_notifications": True,
        "patterns": True,
        "vector_memory": True,
        "inventory_auto_deduct": True,
        "caregiver_role": True,
        "daycare_briefing": True,
        "whatsapp_briefing": True,
        "partner_escalation": True,
        "smartthings": True,
    },
}


async def get_household_tier(db: AsyncSession, household_id) -> str:
    from models.subscription import Subscription

    result = await db.execute(
        select(Subscription).where(Subscription.household_id == household_id)
    )
    sub = result.scalar_one_or_none()
    if not sub or sub.status not in ("active", "trialing"):
        return "free"
    return sub.tier.value if hasattr(sub.tier, "value") else sub.tier


def require_feature(feature: str):
    """Dependency that checks if the household has access to a feature."""

    async def _guard(
        db: AsyncSession = Depends(get_db),
        current_member=Depends(get_current_member),
    ):
        tier = await get_household_tier(db, current_member.household_id)
        features = TIER_FEATURES.get(tier, TIER_FEATURES["free"])

        if not features.get(feature, False):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "FEATURE_NOT_AVAILABLE",
                    "message": f"Deze functie is niet beschikbaar in je huidige abonnement ({tier}).",
                    "required_tier": _minimum_tier_for(feature),
                    "current_tier": tier,
                },
            )
        return tier

    return _guard


def require_member_limit():
    """Dependency that checks if the member limit is not exceeded."""

    async def _guard(
        db: AsyncSession = Depends(get_db),
        current_member=Depends(get_current_member),
    ):
        tier = await get_household_tier(db, current_member.household_id)
        max_members = TIER_FEATURES[tier]["max_members"]
        if max_members is None:
            return

        from models.member import Member

        count = await db.scalar(
            select(func.count()).where(Member.household_id == current_member.household_id)
        )
        if count >= max_members:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "MEMBER_LIMIT_REACHED",
                    "message": f"Je huishouden heeft het maximum van {max_members} leden bereikt.",
                    "current_tier": tier,
                },
            )

    return _guard


def _minimum_tier_for(feature: str) -> str:
    for tier in ["free", "standard", "family"]:
        if TIER_FEATURES[tier].get(feature, False):
            return tier
    return "family"
