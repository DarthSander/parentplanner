import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.rate_limiter import limiter
from models.chat import ChatMessage
from models.member import Member
from schemas.chat import ChatMessageResponse, ChatRequest, ChatResponse
from services.ai.ai_utils import AICallError, call_claude

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ChatResponse)
@limiter.limit("20/minute")
async def send_chat_message(
    request: Request,
    payload: ChatRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and get AI response."""
    # Get recent chat history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.household_id == member.household_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    recent = list(reversed(result.scalars().all()))

    messages = [{"role": msg.role, "content": msg.content} for msg in recent]
    messages.append({"role": "user", "content": payload.message})

    system_prompt = (
        "Je bent de persoonlijke gezinsassistent van dit huishouden. "
        "Je kent de situatie goed en denkt actief mee. "
        "Antwoord altijd in het Nederlands. Wees direct, concreet en eerlijk."
    )

    try:
        reply = await call_claude(
            system=system_prompt,
            user_message=payload.message,
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=messages,
        )
    except AICallError as e:
        logger.error(f"Chat failed: {e}")
        reply = "Sorry, ik kan even niet antwoorden. Probeer het over een paar seconden opnieuw."

    # Save both messages
    user_msg = ChatMessage(
        household_id=member.household_id,
        member_id=member.id,
        role="user",
        content=payload.message,
    )
    assistant_msg = ChatMessage(
        household_id=member.household_id,
        member_id=member.id,
        role="assistant",
        content=reply,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        reply=reply,
        message_id=assistant_msg.id,
        created_at=assistant_msg.created_at,
    )


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_chat_history(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.household_id == member.household_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
    )
    return list(reversed(result.scalars().all()))
