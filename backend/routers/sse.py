"""
Server-Sent Events (SSE) endpoint — replaces Supabase Realtime.

Architecture:
- In-memory pub/sub using asyncio Queues.
- Tasks and inventory routers call `publish_event()` after mutations.
- SSE clients receive a stream of JSON events for their household.
- 30-second keepalive pings prevent proxies from closing idle connections.

Scaling note: for multi-process deployments (multiple Uvicorn workers or
separate machines), replace the in-memory dict with Redis pub/sub using
`aioredis` — subscribe in the SSE generator, publish via a shared Redis
channel named `household:{household_id}`.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import _decode_token
from models.member import Member

logger = logging.getLogger(__name__)

router = APIRouter()

# household_id (str) -> list of asyncio Queues (one per connected SSE client)
_subscribers: dict[str, list[asyncio.Queue]] = {}


def publish_event(household_id: str, event_type: str, data: dict) -> None:
    """
    Publish a realtime event to all SSE subscribers of a household.
    Call this from routers after database mutations.

    event_type examples: "task.created", "task.updated", "task.deleted",
                         "inventory.updated", "inventory.created", "inventory.deleted"
    """
    queues = _subscribers.get(household_id, [])
    for queue in queues:
        try:
            queue.put_nowait({"event": event_type, "data": data})
        except asyncio.QueueFull:
            # Slow consumer — drop the event rather than blocking
            logger.warning(f"SSE queue full for household {household_id}, dropping event {event_type}")


async def _generate_events(
    household_id: str,
    queue: asyncio.Queue,
    request: Request,
) -> AsyncGenerator[str, None]:
    while True:
        if await request.is_disconnected():
            break
        try:
            event = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        except asyncio.TimeoutError:
            # Keepalive ping — prevents proxy/load-balancer from closing idle connections
            yield ": ping\n\n"


async def _get_member_from_token(token: str, db: AsyncSession) -> Member:
    """Resolve a Member from a raw JWT string (used for EventSource query-param auth)."""
    payload = _decode_token(token, "access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldig token.")
    user_id = UUID(user_id_str)

    result = await db.execute(select(Member).where(Member.user_id == user_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Je bent nog geen lid van een huishouden.",
        )
    return member


@router.get("")
async def sse_stream(
    request: Request,
    token: str = Query(..., description="Bearer access token (EventSource cannot set headers)"),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE stream for realtime household updates.
    Connect once per client session; reconnect automatically on disconnect.

    Events emitted:
      task.created / task.updated / task.deleted
      inventory.created / inventory.updated / inventory.deleted
    """
    member = await _get_member_from_token(token, db)
    household_id = str(member.household_id)
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)

    _subscribers.setdefault(household_id, []).append(queue)

    async def generate():
        try:
            async for chunk in _generate_events(household_id, queue, request):
                yield chunk
        finally:
            try:
                _subscribers[household_id].remove(queue)
                if not _subscribers[household_id]:
                    del _subscribers[household_id]
            except (KeyError, ValueError):
                pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
        },
    )
