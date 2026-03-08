"""
SmartThings device sync and status management.

Handles fetching devices, classifying them by type, detecting state changes,
and syncing device data to the local database.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.smartthings import DeviceType, SmartThingsDevice, SmartThingsIntegration
from services.smartthings.auth import SMARTTHINGS_API_BASE, get_valid_access_token

logger = logging.getLogger(__name__)

# Capability → device type mapping
CAPABILITY_DEVICE_MAP = {
    "washerOperatingState": DeviceType.washer,
    "washerMode": DeviceType.washer,
    "dryerOperatingState": DeviceType.dryer,
    "dryerMode": DeviceType.dryer,
    "dishwasherOperatingState": DeviceType.dishwasher,
    "robotCleanerMovement": DeviceType.robot_vacuum,
    "robotCleanerCleaningMode": DeviceType.robot_vacuum,
    "refrigeration": DeviceType.refrigerator,
    "thermostatCoolingSetpoint": DeviceType.refrigerator,
    "ovenOperatingState": DeviceType.oven,
    "ovenMode": DeviceType.oven,
    "airQualitySensor": DeviceType.air_purifier,
    "dustSensor": DeviceType.air_purifier,
}

# States that indicate a device is running a cycle
RUNNING_STATES = {
    DeviceType.washer: {"run", "running"},
    DeviceType.dryer: {"run", "running"},
    DeviceType.dishwasher: {"run", "running"},
    DeviceType.robot_vacuum: {"cleaning", "homing"},
}

# States that indicate a cycle just completed
COMPLETED_STATES = {
    DeviceType.washer: {"stop", "none", "weightSensing", "coolDown"},
    DeviceType.dryer: {"stop", "none", "finished", "coolDown"},
    DeviceType.dishwasher: {"stop", "none", "finished"},
    DeviceType.robot_vacuum: {"idle", "charging"},
}


def classify_device(capabilities: list[str]) -> DeviceType:
    """Determine device type based on its SmartThings capabilities."""
    for cap in capabilities:
        if cap in CAPABILITY_DEVICE_MAP:
            return CAPABILITY_DEVICE_MAP[cap]
    return DeviceType.other


async def fetch_devices(access_token: str) -> list[dict]:
    """Fetch all devices from SmartThings API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SMARTTHINGS_API_BASE}/devices",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json().get("items", [])


async def fetch_device_status(access_token: str, device_id: str) -> dict:
    """Fetch current status of a specific device."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SMARTTHINGS_API_BASE}/devices/{device_id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def sync_devices(db: AsyncSession, integration: SmartThingsIntegration) -> dict:
    """
    Sync all devices from SmartThings to local database.
    Returns counts of created, updated, and removed devices.
    """
    access_token = await get_valid_access_token(db, integration)
    raw_devices = await fetch_devices(access_token)

    created = updated = 0
    seen_external_ids = set()

    for raw in raw_devices:
        external_id = raw["deviceId"]
        seen_external_ids.add(external_id)

        capability_names = []
        for component in raw.get("components", []):
            for cap in component.get("capabilities", []):
                capability_names.append(cap["id"])

        device_type = classify_device(capability_names)
        label = raw.get("label") or raw.get("name", "Unknown Device")
        room = raw.get("roomId")

        # Check if device already exists
        result = await db.execute(
            select(SmartThingsDevice).where(
                SmartThingsDevice.integration_id == integration.id,
                SmartThingsDevice.external_device_id == external_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.label = label
            existing.capabilities = capability_names
            existing.device_type = device_type
            if room:
                existing.room = room
            updated += 1
        else:
            device = SmartThingsDevice(
                household_id=integration.household_id,
                integration_id=integration.id,
                external_device_id=external_id,
                device_type=device_type,
                label=label,
                room=room,
                capabilities=capability_names,
            )
            db.add(device)
            created += 1

    integration.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    return {"created": created, "updated": updated}


def detect_cycle_change(device: SmartThingsDevice, new_state: dict) -> str | None:
    """
    Compare old and new device state to detect cycle transitions.

    Returns:
        'cycle_started' if device started running
        'cycle_completed' if device stopped running
        None if no cycle change
    """
    if device.device_type not in RUNNING_STATES:
        return None

    machine_state = _extract_machine_state(device.device_type, new_state)
    if machine_state is None:
        return None

    running_values = RUNNING_STATES[device.device_type]
    was_running = device.is_running

    is_now_running = machine_state.lower() in running_values

    if not was_running and is_now_running:
        return "cycle_started"
    elif was_running and not is_now_running:
        return "cycle_completed"

    return None


def _extract_machine_state(device_type: DeviceType, status: dict) -> str | None:
    """Extract the machine state from a SmartThings device status response."""
    components = status.get("components", {})
    main = components.get("main", {})

    state_capability_map = {
        DeviceType.washer: ("washerOperatingState", "machineState"),
        DeviceType.dryer: ("dryerOperatingState", "machineState"),
        DeviceType.dishwasher: ("dishwasherOperatingState", "machineState"),
        DeviceType.robot_vacuum: ("robotCleanerMovement", "robotCleanerMovement"),
    }

    cap_name, attr_name = state_capability_map.get(device_type, (None, None))
    if not cap_name:
        return None

    capability = main.get(cap_name, {})
    state_obj = capability.get(attr_name, {})
    return state_obj.get("value")


def extract_completion_time(device_type: DeviceType, status: dict) -> str | None:
    """Extract estimated completion time from device status."""
    components = status.get("components", {})
    main = components.get("main", {})

    cap_map = {
        DeviceType.washer: "washerOperatingState",
        DeviceType.dryer: "dryerOperatingState",
        DeviceType.dishwasher: "dishwasherOperatingState",
    }

    cap_name = cap_map.get(device_type)
    if not cap_name:
        return None

    capability = main.get(cap_name, {})
    return capability.get("completionTime", {}).get("value")
