from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.rate_limiter import limiter

# Sentry for error tracking (production only)
if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )

app = FastAPI(title="GezinsAI API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
from routers import (  # noqa: E402
    account, auth, calendar, chat, health, households, inventory,
    members, notifications, onboarding, patterns,
    sse, subscriptions, sync, tasks, webhooks,
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(households.router, prefix="/households", tags=["households"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(account.router, prefix="/account", tags=["account"])
app.include_router(sse.router, prefix="/sse", tags=["sse"])
