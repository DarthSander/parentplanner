import logging
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()

# Supabase JWKS endpoint for JWT verification
_supabase_jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwks_cache: dict | None = None


async def _get_supabase_jwks() -> dict:
    """Fetch and cache Supabase JWKS for JWT verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    async with httpx.AsyncClient() as client:
        response = await client.get(_supabase_jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


def _decode_supabase_jwt(token: str) -> dict:
    """
    Decode and verify a Supabase JWT token.
    Uses the JWT_SECRET (Supabase JWT secret) for HS256 verification.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is verlopen.",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ongeldig token.",
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UUID:
    """
    Extract and verify the user ID from the Supabase JWT.
    Returns the Supabase auth.users UUID.
    """
    payload = _decode_supabase_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bevat geen gebruikers-ID.",
        )
    return UUID(user_id)
