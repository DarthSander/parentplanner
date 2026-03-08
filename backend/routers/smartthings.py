"""
SmartThings API router.

Handles OAuth flow, device management, consumable linking, and event history.
All endpoints (except webhook) require family tier subscription.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.encryption import encrypt_token
from core.subscription_guard import require_feature
from models.inventory import InventoryItem
from models.member import Member
from models.smartthings import (
    DeviceConsumable,
    DeviceEvent,
    SmartThingsDevice,
    SmartThingsIntegration,
)
from schemas.smartthings import (
    ConsumableCreate,
    ConsumableResponse,
    ConsumableUpdate,
    DeviceEventResponse,
    DeviceResponse,
    DeviceStatsResponse,
    DeviceUpdate,
    SmartThingsAuthURL,
    SmartThingsCallback,
    SmartThingsStatusResponse,
)
from services.smartthings.auth import (
    exchange_code_for_tokens,
    get_smartthings_auth_url,
    get_valid_access_token,
)
from services.smartthings.devices import fetch_device_status, sync_devices

logger = logging.getLogger(__name__)

router = APIRouter()


# ── OAuth & Integration ─────────────────────────────────────────────────────


@router.get("/auth-url", response_model=SmartThingsAuthURL)
async def get_auth_url(
    redirect_uri: str,
    member: Member = Depends(get_current_member),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Generate SmartThings OAuth2 authorization URL."""
    state = secrets.token_urlsafe(32)
    auth_url = get_smartthings_auth_url(redirect_uri, state)
    return SmartThingsAuthURL(auth_url=auth_url)


@router.post("/callback")
async def oauth_callback(
    payload: SmartThingsCallback,
    redirect_uri: str,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Exchange authorization code for tokens and create integration."""
    # Check if integration already exists
    existing = await db.execute(
        select(SmartThingsIntegration).where(
            SmartThingsIntegration.household_id == member.household_id,
            SmartThingsIntegration.sync_enabled == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SmartThings is al gekoppeld aan dit huishouden.",
        )

    tokens = await exchange_code_for_tokens(payload.code, redirect_uri)

    integration = SmartThingsIntegration(
        household_id=member.household_id,
        member_id=member.id,
        access_token=encrypt_token(tokens["access_token"]),
        refresh_token=encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else None,
        token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"]),
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)

    # Sync devices immediately
    try:
        sync_result = await sync_devices(db, integration)
        logger.info(f"Initial SmartThings sync: {sync_result}")
    except Exception as e:
        logger.error(f"Initial device sync failed: {e}")

    return {"message": "SmartThings gekoppeld!", "devices_synced": True}


@router.get("/status", response_model=SmartThingsStatusResponse)
async def get_status(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Get SmartThings integration status."""
    result = await db.execute(
        select(SmartThingsIntegration).where(
            SmartThingsIntegration.household_id == member.household_id,
            SmartThingsIntegration.sync_enabled == True,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        return SmartThingsStatusResponse(connected=False)

    device_count = await db.scalar(
        select(func.count()).where(
            SmartThingsDevice.integration_id == integration.id
        )
    )

    return SmartThingsStatusResponse(
        connected=True,
        location_id=integration.location_id,
        last_synced_at=integration.last_synced_at,
        device_count=device_count or 0,
    )


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Disconnect SmartThings integration."""
    result = await db.execute(
        select(SmartThingsIntegration).where(
            SmartThingsIntegration.household_id == member.household_id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(integration)
    await db.commit()


# ── Devices ──────────────────────────────────────────────────────────────────


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """List all SmartThings devices for the household."""
    result = await db.execute(
        select(SmartThingsDevice)
        .where(SmartThingsDevice.household_id == member.household_id)
        .order_by(SmartThingsDevice.label)
    )
    return result.scalars().all()


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Get device details including current status."""
    result = await db.execute(
        select(SmartThingsDevice).where(
            SmartThingsDevice.id == device_id,
            SmartThingsDevice.household_id == member.household_id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return device


@router.post("/devices/{device_id}/sync", response_model=DeviceResponse)
async def sync_device_status(
    device_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Manually refresh a device's status from SmartThings."""
    result = await db.execute(
        select(SmartThingsDevice).where(
            SmartThingsDevice.id == device_id,
            SmartThingsDevice.household_id == member.household_id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    integration_result = await db.execute(
        select(SmartThingsIntegration).where(SmartThingsIntegration.id == device.integration_id)
    )
    integration = integration_result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    access_token = await get_valid_access_token(db, integration)
    new_status = await fetch_device_status(access_token, device.external_device_id)
    device.current_state = new_status
    device.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(device)
    return device


@router.patch("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    payload: DeviceUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Update device label, room, or sync status."""
    result = await db.execute(
        select(SmartThingsDevice).where(
            SmartThingsDevice.id == device_id,
            SmartThingsDevice.household_id == member.household_id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    device.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(device)
    return device


# ── Consumables ──────────────────────────────────────────────────────────────


@router.get("/devices/{device_id}/consumables", response_model=list[ConsumableResponse])
async def list_consumables(
    device_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """List consumables linked to a device."""
    # Verify device belongs to household
    device = await _get_device_or_404(db, device_id, member.household_id)

    result = await db.execute(
        select(DeviceConsumable).where(DeviceConsumable.device_id == device.id)
    )
    consumables = result.scalars().all()

    # Enrich with inventory item names
    response = []
    for c in consumables:
        item_result = await db.execute(select(InventoryItem).where(InventoryItem.id == c.inventory_item_id))
        item = item_result.scalar_one_or_none()
        response.append(ConsumableResponse(
            id=c.id,
            device_id=c.device_id,
            inventory_item_id=c.inventory_item_id,
            inventory_item_name=item.name if item else None,
            usage_per_cycle=float(c.usage_per_cycle),
            auto_deduct=c.auto_deduct,
            created_at=c.created_at,
        ))
    return response


@router.post("/devices/{device_id}/consumables", response_model=ConsumableResponse, status_code=status.HTTP_201_CREATED)
async def link_consumable(
    device_id: UUID,
    payload: ConsumableCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Link an inventory item as a consumable to a device."""
    device = await _get_device_or_404(db, device_id, member.household_id)

    # Verify inventory item belongs to same household
    item_result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == payload.inventory_item_id,
            InventoryItem.household_id == member.household_id,
        )
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voorraaditem niet gevonden.")

    # Check if already linked
    existing = await db.execute(
        select(DeviceConsumable).where(
            DeviceConsumable.device_id == device.id,
            DeviceConsumable.inventory_item_id == payload.inventory_item_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dit item is al gekoppeld aan dit apparaat.")

    consumable = DeviceConsumable(
        device_id=device.id,
        inventory_item_id=payload.inventory_item_id,
        usage_per_cycle=payload.usage_per_cycle,
        auto_deduct=payload.auto_deduct,
    )
    db.add(consumable)
    await db.commit()
    await db.refresh(consumable)

    return ConsumableResponse(
        id=consumable.id,
        device_id=consumable.device_id,
        inventory_item_id=consumable.inventory_item_id,
        inventory_item_name=item.name,
        usage_per_cycle=float(consumable.usage_per_cycle),
        auto_deduct=consumable.auto_deduct,
        created_at=consumable.created_at,
    )


@router.patch("/consumables/{consumable_id}", response_model=ConsumableResponse)
async def update_consumable(
    consumable_id: UUID,
    payload: ConsumableUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Update consumable settings (usage per cycle, auto deduct)."""
    result = await db.execute(
        select(DeviceConsumable)
        .join(SmartThingsDevice)
        .where(
            DeviceConsumable.id == consumable_id,
            SmartThingsDevice.household_id == member.household_id,
        )
    )
    consumable = result.scalar_one_or_none()
    if not consumable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(consumable, field, value)
    await db.commit()
    await db.refresh(consumable)

    item_result = await db.execute(select(InventoryItem).where(InventoryItem.id == consumable.inventory_item_id))
    item = item_result.scalar_one_or_none()

    return ConsumableResponse(
        id=consumable.id,
        device_id=consumable.device_id,
        inventory_item_id=consumable.inventory_item_id,
        inventory_item_name=item.name if item else None,
        usage_per_cycle=float(consumable.usage_per_cycle),
        auto_deduct=consumable.auto_deduct,
        created_at=consumable.created_at,
    )


@router.delete("/consumables/{consumable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_consumable(
    consumable_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Unlink a consumable from a device."""
    result = await db.execute(
        select(DeviceConsumable)
        .join(SmartThingsDevice)
        .where(
            DeviceConsumable.id == consumable_id,
            SmartThingsDevice.household_id == member.household_id,
        )
    )
    consumable = result.scalar_one_or_none()
    if not consumable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(consumable)
    await db.commit()


# ── Events & Stats ───────────────────────────────────────────────────────────


@router.get("/devices/{device_id}/events", response_model=list[DeviceEventResponse])
async def list_device_events(
    device_id: UUID,
    limit: int = 50,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Get event history for a device."""
    device = await _get_device_or_404(db, device_id, member.household_id)

    result = await db.execute(
        select(DeviceEvent)
        .where(DeviceEvent.device_id == device.id)
        .order_by(DeviceEvent.created_at.desc())
        .limit(min(limit, 200))
    )
    return result.scalars().all()


@router.get("/devices/{device_id}/stats", response_model=DeviceStatsResponse)
async def get_device_stats(
    device_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
    _tier: str = Depends(require_feature("smartthings")),
):
    """Get usage statistics for a device."""
    device = await _get_device_or_404(db, device_id, member.household_id)
    now = datetime.now(timezone.utc)

    # Cycles this week
    week_ago = now - timedelta(days=7)
    cycles_week = await db.scalar(
        select(func.count()).where(
            DeviceEvent.device_id == device.id,
            DeviceEvent.event_type == "cycle_completed",
            DeviceEvent.created_at >= week_ago,
        )
    ) or 0

    # Cycles this month
    month_ago = now - timedelta(days=30)
    cycles_month = await db.scalar(
        select(func.count()).where(
            DeviceEvent.device_id == device.id,
            DeviceEvent.event_type == "cycle_completed",
            DeviceEvent.created_at >= month_ago,
        )
    ) or 0

    # Average cycles per week (based on total history)
    first_event = await db.scalar(
        select(func.min(DeviceEvent.created_at)).where(DeviceEvent.device_id == device.id)
    )
    if first_event:
        weeks_active = max(1, (now - first_event).days / 7)
        avg_per_week = device.total_cycles / weeks_active
    else:
        avg_per_week = 0

    # Consumables status
    consumables_result = await db.execute(
        select(DeviceConsumable).where(DeviceConsumable.device_id == device.id)
    )
    consumables_status = []
    for c in consumables_result.scalars():
        item_result = await db.execute(select(InventoryItem).where(InventoryItem.id == c.inventory_item_id))
        item = item_result.scalar_one_or_none()
        if item:
            cycles_remaining = float(item.current_quantity) / float(c.usage_per_cycle) if c.usage_per_cycle else 0
            consumables_status.append({
                "name": item.name,
                "current_quantity": float(item.current_quantity),
                "unit": item.unit,
                "usage_per_cycle": float(c.usage_per_cycle),
                "cycles_remaining": int(cycles_remaining),
                "is_low": float(item.current_quantity) <= float(item.threshold_quantity),
            })

    return DeviceStatsResponse(
        total_cycles=device.total_cycles,
        cycles_this_week=cycles_week,
        cycles_this_month=cycles_month,
        avg_cycles_per_week=round(avg_per_week, 1),
        consumables_status=consumables_status,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _get_device_or_404(db: AsyncSession, device_id: UUID, household_id) -> SmartThingsDevice:
    result = await db.execute(
        select(SmartThingsDevice).where(
            SmartThingsDevice.id == device_id,
            SmartThingsDevice.household_id == household_id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return device
