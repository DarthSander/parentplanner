"""
SmartThings webhook handler.

Processes incoming SmartThings lifecycle and device events.
SmartThings sends DEVICE_EVENT when device state changes.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.smartthings import SmartThingsDevice, SmartThingsIntegration
from services.smartthings.devices import detect_cycle_change
from services.smartthings.events import (
    process_cycle_completed,
    process_cycle_started,
    process_door_event,
    process_error_event,
    process_filter_alert,
)

logger = logging.getLogger(__name__)


async def handle_smartthings_webhook(db: AsyncSession, payload: dict) -> dict:
    """
    Process a SmartThings webhook event.

    SmartThings lifecycle events:
    - CONFIRMATION: verify webhook URL
    - CONFIGURATION: app configuration
    - INSTALL / UPDATE / UNINSTALL: app lifecycle
    - EVENT: device state changes
    """
    lifecycle = payload.get("lifecycle")

    if lifecycle == "CONFIRMATION":
        # Return the confirmationUrl as-is for SmartThings to verify
        return {"targetUrl": payload.get("confirmationData", {}).get("confirmationUrl")}

    if lifecycle == "CONFIGURATION":
        return _handle_configuration(payload)

    if lifecycle == "EVENT":
        await _handle_event(db, payload)
        return {"statusCode": 200}

    if lifecycle in ("INSTALL", "UPDATE"):
        return {"statusCode": 200}

    if lifecycle == "UNINSTALL":
        await _handle_uninstall(db, payload)
        return {"statusCode": 200}

    logger.warning(f"Unknown SmartThings lifecycle: {lifecycle}")
    return {"statusCode": 200}


def _handle_configuration(payload: dict) -> dict:
    """Handle configuration lifecycle — return app configuration schema."""
    phase = payload.get("configurationData", {}).get("phase")

    if phase == "INITIALIZE":
        return {
            "configurationData": {
                "initialize": {
                    "name": "GezinsAI SmartThings",
                    "description": "Slimme huishoudelijke apparaten koppelen aan GezinsAI",
                    "id": "gezinsai_smartthings",
                    "permissions": ["r:devices:*", "x:devices:*"],
                    "firstPageId": "1",
                }
            }
        }
    elif phase == "PAGE":
        return {
            "configurationData": {
                "page": {
                    "pageId": "1",
                    "name": "Apparaten selecteren",
                    "sections": [
                        {
                            "name": "Apparaten",
                            "settings": [
                                {
                                    "id": "devices",
                                    "name": "Welke apparaten wil je koppelen?",
                                    "type": "DEVICE",
                                    "required": False,
                                    "multiple": True,
                                    "capabilities": ["washerOperatingState", "dryerOperatingState",
                                                     "dishwasherOperatingState", "robotCleanerMovement",
                                                     "refrigeration", "ovenOperatingState"],
                                }
                            ],
                        }
                    ],
                    "complete": True,
                }
            }
        }

    return {"configurationData": {}}


async def _handle_event(db: AsyncSession, payload: dict):
    """Process device state change events."""
    event_data = payload.get("eventData", {})
    events = event_data.get("events", [])

    for event in events:
        event_type = event.get("eventType")

        if event_type == "DEVICE_EVENT":
            await _handle_device_event(db, event.get("deviceEvent", {}))
        elif event_type == "DEVICE_HEALTH_EVENT":
            device_health = event.get("deviceHealthEvent", {})
            logger.info(f"Device health event: {device_health}")


async def _handle_device_event(db: AsyncSession, device_event: dict):
    """Process a single device event from SmartThings."""
    external_device_id = device_event.get("deviceId")
    if not external_device_id:
        return

    # Find the device in our database
    result = await db.execute(
        select(SmartThingsDevice).where(
            SmartThingsDevice.external_device_id == external_device_id,
            SmartThingsDevice.sync_enabled == True,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        logger.debug(f"Unknown SmartThings device: {external_device_id}")
        return

    capability = device_event.get("capability", "")
    attribute = device_event.get("attribute", "")
    value = device_event.get("value", "")

    logger.info(
        f"Device event: {device.label} — {capability}.{attribute} = {value}"
    )

    # Update current state
    if device.current_state is None:
        device.current_state = {}
    state = dict(device.current_state)
    if capability not in state:
        state[capability] = {}
    state[capability][attribute] = value
    device.current_state = state

    # Detect cycle changes for appliances
    if attribute == "machineState" or attribute == "robotCleanerMovement":
        new_state = {"components": {"main": {capability: {attribute: {"value": value}}}}}
        change = detect_cycle_change(device, new_state)

        if change == "cycle_started":
            await process_cycle_started(db, device)
        elif change == "cycle_completed":
            await process_cycle_completed(db, device)

    # Door events (refrigerator)
    elif capability == "contactSensor" and attribute == "contact":
        await process_door_event(db, device, opened=(value == "open"))

    # Filter alerts
    elif attribute == "filterStatus" and value in ("replace", "dirty", "cleaning"):
        await process_filter_alert(db, device)

    await db.commit()


async def _handle_uninstall(db: AsyncSession, payload: dict):
    """Clean up when SmartThings app is uninstalled."""
    installed_app_id = payload.get("uninstallData", {}).get("installedApp", {}).get("installedAppId")
    if not installed_app_id:
        return

    result = await db.execute(
        select(SmartThingsIntegration).where(
            SmartThingsIntegration.installed_app_id == installed_app_id
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        integration.sync_enabled = False
        await db.commit()
        logger.info(f"SmartThings app uninstalled: {installed_app_id}")
