"""
Picknick authentication service.

Uses the unofficial python-picnic-api library (pip install python-picnic-api).
Credentials (email + password) are stored encrypted with Fernet.
No OAuth2 — just email/password → Picknick API session.

DISCLAIMER: python-picnic-api is an unofficial, community-maintained library.
Picknick can change their internal API at any time without notice.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)


def _get_picnic_client(email: str, password: str, country_code: str = "NL"):
    """
    Create a python-picnic-api client.
    Import is deferred so startup doesn't fail if the package isn't installed.
    """
    try:
        from python_picnic_api import PicnicAPI
        return PicnicAPI(username=email, password=password, country_code=country_code)
    except ImportError:
        raise RuntimeError(
            "python-picnic-api is not installed. Run: pip install python-picnic-api"
        )
    except Exception as e:
        raise ValueError(f"Picknick verbinding mislukt: {e}") from e


async def connect_picknick(
    db: AsyncSession,
    household_id: UUID,
    member_id: UUID,
    email: str,
    password: str,
    country_code: str = "NL",
):
    """
    Validate Picknick credentials and store them encrypted.
    Returns the new PicknickIntegration model instance.
    Raises ValueError when credentials are invalid.
    """
    from models.picknick import PicknickIntegration

    # Test credentials by making a real API call
    client = _get_picnic_client(email, password, country_code)
    try:
        client.get_user()  # raises if credentials are wrong
    except Exception as e:
        raise ValueError(f"Ongeldige Picknick-inloggegevens: {e}") from e

    # Check if integration already exists for this household
    result = await db.execute(
        select(PicknickIntegration).where(PicknickIntegration.household_id == household_id)
    )
    integration = result.scalar_one_or_none()

    if integration:
        # Update existing
        integration.encrypted_email = encrypt_token(email)
        integration.encrypted_password = encrypt_token(password)
        integration.country_code = country_code
        integration.member_id = member_id
    else:
        integration = PicknickIntegration(
            household_id=household_id,
            member_id=member_id,
            encrypted_email=encrypt_token(email),
            encrypted_password=encrypt_token(password),
            country_code=country_code,
        )
        db.add(integration)

    await db.commit()
    await db.refresh(integration)
    return integration


async def get_picknick_client_for_integration(integration):
    """
    Return a ready-to-use PicnicAPI client for a stored integration.
    Credentials are decrypted from the integration model.
    """
    email = decrypt_token(integration.encrypted_email)
    password = decrypt_token(integration.encrypted_password)
    return _get_picnic_client(email, password, integration.country_code)


async def get_integration(db: AsyncSession, household_id: UUID):
    """Retrieve the PicknickIntegration for a household, or None."""
    from models.picknick import PicknickIntegration

    result = await db.execute(
        select(PicknickIntegration).where(PicknickIntegration.household_id == household_id)
    )
    return result.scalar_one_or_none()


async def disconnect_picknick(db: AsyncSession, integration) -> None:
    """Delete the integration and all associated data."""
    await db.delete(integration)
    await db.commit()
