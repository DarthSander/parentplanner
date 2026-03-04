import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from core.config import settings
from core.rate_limiter import limiter
from schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest

logger = logging.getLogger(__name__)

router = APIRouter()

_supabase_auth_url = f"{settings.SUPABASE_URL}/auth/v1"
_headers = {
    "apikey": settings.SUPABASE_SERVICE_KEY,
    "Content-Type": "application/json",
}


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, payload: RegisterRequest):
    """Register a new user via Supabase Auth."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_supabase_auth_url}/signup",
            headers=_headers,
            json={
                "email": payload.email,
                "password": payload.password,
                "data": {"display_name": payload.display_name},
            },
        )

    if response.status_code == 422:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ongeldig e-mailadres of wachtwoord.",
        )

    if response.status_code == 400:
        data = response.json()
        msg = data.get("msg", data.get("error_description", "Registratie mislukt."))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    if response.status_code not in (200, 201):
        logger.error(f"Supabase signup error: {response.status_code} {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Registratie kon niet worden verwerkt.",
        )

    data = response.json()
    session = data.get("session")
    if not session:
        # Email confirmation required — user created but no session yet
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Bevestig je e-mailadres om in te loggen.",
        )

    return AuthResponse(
        access_token=session["access_token"],
        refresh_token=session["refresh_token"],
        expires_in=session.get("expires_in", 3600),
        user_id=data["user"]["id"],
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest):
    """Login via Supabase Auth with email and password."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_supabase_auth_url}/token",
            headers=_headers,
            params={"grant_type": "password"},
            json={
                "email": payload.email,
                "password": payload.password,
            },
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Onjuist e-mailadres of wachtwoord.",
        )

    if response.status_code != 200:
        logger.error(f"Supabase login error: {response.status_code} {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Inloggen kon niet worden verwerkt.",
        )

    data = response.json()
    return AuthResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_in=data.get("expires_in", 3600),
        user_id=data["user"]["id"],
    )


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("10/minute")
async def refresh(request: Request, payload: RefreshRequest):
    """Refresh an expired access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_supabase_auth_url}/token",
            headers=_headers,
            params={"grant_type": "refresh_token"},
            json={"refresh_token": payload.refresh_token},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is ongeldig of verlopen.",
        )

    data = response.json()
    return AuthResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_in=data.get("expires_in", 3600),
        user_id=data["user"]["id"],
    )
