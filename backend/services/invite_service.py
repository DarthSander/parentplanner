import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.household import Household
from models.member import Member

logger = logging.getLogger(__name__)


async def create_invite(
    db: AsyncSession,
    household_id: UUID,
    inviter_name: str,
    email: str,
    role: str,
    display_name: str,
) -> str:
    """Generate an invite token and send invitation email."""
    token_payload = {
        "household_id": str(household_id),
        "email": email,
        "role": role,
        "display_name": display_name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_TOKEN_EXPIRY_HOURS),
        "type": "household_invite",
    }
    token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm="HS256")

    # TODO: Send email via Resend when notification/email service is implemented (step 9)
    invite_url = f"{settings.ALLOWED_ORIGINS[0]}/invite/accept?token={token}"
    logger.info(f"Invite created for {email} to household {household_id}: {invite_url}")

    return token


def validate_invite_token(token: str) -> dict:
    """Validate an invite token without accepting it."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Deze uitnodiging is verlopen.")
    except jwt.InvalidTokenError:
        raise ValueError("Ongeldige uitnodiging.")

    if payload.get("type") != "household_invite":
        raise ValueError("Ongeldig token type.")

    return payload


async def accept_invite(db: AsyncSession, token: str, user_id: UUID) -> Member:
    """Validate the invite token and add the user to the household."""
    payload = validate_invite_token(token)

    # Check if user is already a member
    result = await db.execute(
        select(Member).where(
            Member.household_id == payload["household_id"],
            Member.user_id == user_id,
        )
    )
    if result.scalar_one_or_none():
        raise ValueError("Je bent al lid van dit huishouden.")

    member = Member(
        household_id=payload["household_id"],
        user_id=user_id,
        role=payload["role"],
        display_name=payload["display_name"],
        email=payload["email"],
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member
