"""
Samsung SmartThings OAuth2 flow.

SmartThings uses standard OAuth2 authorization code flow.
Docs: https://developer-preview.smartthings.com/docs/connected-services/hosting/authorization
"""
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

SMARTTHINGS_AUTH_URL = "https://api.smartthings.com/oauth/authorize"
SMARTTHINGS_TOKEN_URL = "https://auth-global.api.smartthings.com/oauth/token"
SMARTTHINGS_API_BASE = "https://api.smartthings.com/v1"

SCOPES = "r:devices:* x:devices:* r:locations:* r:installedapps"


def get_smartthings_auth_url(redirect_uri: str, state: str) -> str:
    """Generate SmartThings OAuth2 authorization URL."""
    params = {
        "client_id": settings.SMARTTHINGS_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    return f"{SMARTTHINGS_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SMARTTHINGS_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.SMARTTHINGS_CLIENT_ID,
                "client_secret": settings.SMARTTHINGS_CLIENT_SECRET,
            },
        )
        response.raise_for_status()
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in", 86400),
        }


async def refresh_access_token(refresh_token_encrypted: str) -> dict:
    """Refresh an expired access token."""
    refresh_token = decrypt_token(refresh_token_encrypted)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SMARTTHINGS_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.SMARTTHINGS_CLIENT_ID,
                "client_secret": settings.SMARTTHINGS_CLIENT_SECRET,
            },
        )
        response.raise_for_status()
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", refresh_token),
            "expires_in": data.get("expires_in", 86400),
        }


async def get_valid_access_token(db: AsyncSession, integration) -> str:
    """Get a valid access token, refreshing if needed (5-min buffer)."""
    now = datetime.now(timezone.utc)

    if integration.token_expires_at and integration.token_expires_at > now + timedelta(minutes=5):
        return decrypt_token(integration.access_token)

    if not integration.refresh_token:
        raise ValueError("No refresh token available. Re-authorization needed.")

    tokens = await refresh_access_token(integration.refresh_token)
    integration.access_token = encrypt_token(tokens["access_token"])
    if tokens.get("refresh_token"):
        integration.refresh_token = encrypt_token(tokens["refresh_token"])
    integration.token_expires_at = now + timedelta(seconds=tokens["expires_in"])
    await db.commit()

    return tokens["access_token"]
