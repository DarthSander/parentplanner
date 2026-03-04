import logging

from fastapi import APIRouter, Request, status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    # TODO: Implement Stripe webhook processing (step 15)
    body = await request.body()
    logger.info(f"Stripe webhook received: {len(body)} bytes")
    return {"received": True}


@router.post("/calendar")
async def calendar_webhook(request: Request):
    """Handle calendar sync webhook events (Google Calendar push notifications)."""
    # TODO: Implement calendar webhook processing (step 7)
    return {"received": True}
