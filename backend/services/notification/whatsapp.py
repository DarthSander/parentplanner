import logging

from core.config import settings

logger = logging.getLogger(__name__)


async def send_whatsapp_message(to_phone: str, body: str) -> bool:
    """Send a WhatsApp message via Twilio."""
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            body=body,
            to=f"whatsapp:{to_phone}",
        )
        logger.info(f"WhatsApp sent to {to_phone}: SID {message.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed to {to_phone}: {e}")
        return False
