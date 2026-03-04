from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["100/minute"],
)

# Rate limits per endpoint category:
#
# Default:              100 requests/minute per IP
# Auth endpoints:       10 requests/minute per IP  (brute force prevention)
# Chat endpoint:        20 requests/minute per user (Claude API costs)
# Sync endpoint:        30 requests/minute per user (batch operations)
# Webhooks:             no limit (from Stripe/Google)
# Pattern analyze-now:  5 requests/hour per user (heavy AI operation)
