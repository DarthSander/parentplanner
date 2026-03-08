"""
SmartThings event processing.

Handles cycle completion, consumable deduction, inventory alerts,
AI task generation, and notifications when device events occur.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory import InventoryAlert, InventoryItem
from models.smartthings import DeviceConsumable, DeviceEvent, DeviceEventType, SmartThingsDevice
from models.task import Task
from routers.sse import publish_event
from services.vector.embeddings import build_device_event_document

logger = logging.getLogger(__name__)


async def process_cycle_started(db: AsyncSession, device: SmartThingsDevice):
    """Record cycle start and send notification."""
    now = datetime.now(timezone.utc)

    device.is_running = True
    device.cycle_started_at = now
    device.last_event_at = now

    event = DeviceEvent(
        device_id=device.id,
        household_id=device.household_id,
        event_type=DeviceEventType.cycle_started,
        event_data={"device_label": device.label, "device_type": device.device_type.value},
    )
    db.add(event)
    await db.commit()

    publish_event(
        str(device.household_id),
        "device.cycle_started",
        {"device_id": str(device.id), "label": device.label, "type": device.device_type.value},
    )

    logger.info(f"Cycle started: {device.label} (household {device.household_id})")


async def process_cycle_completed(db: AsyncSession, device: SmartThingsDevice):
    """
    Handle cycle completion:
    1. Record event
    2. Increment cycle counter
    3. Deduct linked consumables
    4. Check inventory thresholds → create alerts
    5. Generate AI tasks if stock is low
    6. Send notification
    7. Queue vector embedding
    """
    now = datetime.now(timezone.utc)

    # 1. Record event
    duration_minutes = None
    if device.cycle_started_at:
        duration_minutes = int((now - device.cycle_started_at).total_seconds() / 60)

    event = DeviceEvent(
        device_id=device.id,
        household_id=device.household_id,
        event_type=DeviceEventType.cycle_completed,
        event_data={
            "device_label": device.label,
            "device_type": device.device_type.value,
            "duration_minutes": duration_minutes,
        },
    )
    db.add(event)

    # 2. Update device state
    device.is_running = False
    device.total_cycles += 1
    device.last_event_at = now
    device.cycle_started_at = None

    # 3. Deduct consumables
    consumables_result = await db.execute(
        select(DeviceConsumable).where(
            DeviceConsumable.device_id == device.id,
            DeviceConsumable.auto_deduct == True,
        )
    )
    consumables = consumables_result.scalars().all()

    low_stock_items = []

    for consumable in consumables:
        item_result = await db.execute(
            select(InventoryItem).where(InventoryItem.id == consumable.inventory_item_id)
        )
        item = item_result.scalar_one_or_none()
        if not item:
            continue

        # Deduct usage
        item.current_quantity = max(0, float(item.current_quantity) - float(consumable.usage_per_cycle))
        item.updated_at = now

        # Update consumption rate (running average)
        if item.average_consumption_rate:
            item.average_consumption_rate = (float(item.average_consumption_rate) * 0.9 +
                                              float(consumable.usage_per_cycle) * 0.1)
        else:
            item.average_consumption_rate = float(consumable.usage_per_cycle)

        # 4. Check threshold
        if float(item.current_quantity) <= float(item.threshold_quantity):
            # Check if unresolved alert already exists
            existing_alert = await db.execute(
                select(InventoryAlert).where(
                    InventoryAlert.item_id == item.id,
                    InventoryAlert.resolved == False,
                )
            )
            if not existing_alert.scalar_one_or_none():
                alert_type = "out_of_stock" if item.current_quantity <= 0 else "low_stock"
                alert = InventoryAlert(
                    item_id=item.id,
                    household_id=device.household_id,
                    alert_type=alert_type,
                    message=f"{item.name} is bijna op (nog {item.current_quantity} {item.unit}). "
                            f"Automatisch afgeschreven door {device.label}.",
                )
                db.add(alert)
                low_stock_items.append(item)

        publish_event(
            str(device.household_id),
            "inventory.updated",
            {"id": str(item.id)},
        )

    # 5. Generate task for low stock items
    for item in low_stock_items:
        # Check if similar task already exists and is open
        existing_task = await db.execute(
            select(Task).where(
                Task.household_id == device.household_id,
                Task.title.ilike(f"%{item.name}%boodschappen%"),
                Task.status.in_(["open", "in_progress"]),
            )
        )
        if not existing_task.scalar_one_or_none():
            remaining_info = ""
            if item.average_consumption_rate and item.average_consumption_rate > 0:
                cycles_left = float(item.current_quantity) / float(item.average_consumption_rate)
                remaining_info = f" (nog ~{int(cycles_left)} wasbeurten)"

            task = Task(
                household_id=device.household_id,
                title=f"{item.name} op boodschappenlijst zetten",
                description=f"{item.name} is bijna op: nog {item.current_quantity} {item.unit}{remaining_info}. "
                            f"Automatisch gedetecteerd door {device.label}.",
                category="household",
                task_type="quick",
                ai_generated=True,
            )
            db.add(task)

    await db.commit()

    # 6. Send notification
    device_labels = {
        "washer": "Wasmachine",
        "dryer": "Droger",
        "dishwasher": "Vaatwasser",
        "robot_vacuum": "Robotstofzuiger",
    }
    device_label = device_labels.get(device.device_type.value, device.label)
    duration_str = f" ({duration_minutes} minuten)" if duration_minutes else ""

    publish_event(
        str(device.household_id),
        "device.cycle_completed",
        {
            "device_id": str(device.id),
            "label": device.label,
            "type": device.device_type.value,
            "message": f"{device_label} is klaar!{duration_str}",
            "low_stock": [{"name": i.name, "quantity": float(i.current_quantity), "unit": i.unit} for i in low_stock_items],
        },
    )

    # 7. Queue vector embedding
    try:
        from workers.tasks.embed_document import embed_document
        embed_document.delay(str(event.id), "device_event")
    except Exception as e:
        logger.warning(f"Failed to queue embedding for device event: {e}")

    logger.info(
        f"Cycle completed: {device.label} (total: {device.total_cycles}, "
        f"low stock items: {len(low_stock_items)})"
    )


async def process_door_event(db: AsyncSession, device: SmartThingsDevice, opened: bool):
    """Track door open/close events (primarily for refrigerator)."""
    now = datetime.now(timezone.utc)

    event = DeviceEvent(
        device_id=device.id,
        household_id=device.household_id,
        event_type=DeviceEventType.door_opened if opened else DeviceEventType.door_closed,
        event_data={"device_label": device.label},
    )
    db.add(event)
    device.last_event_at = now
    await db.commit()


async def process_error_event(db: AsyncSession, device: SmartThingsDevice, error_data: dict):
    """Record device error and notify household."""
    now = datetime.now(timezone.utc)

    event = DeviceEvent(
        device_id=device.id,
        household_id=device.household_id,
        event_type=DeviceEventType.error,
        event_data={**error_data, "device_label": device.label},
    )
    db.add(event)
    device.last_event_at = now
    await db.commit()

    publish_event(
        str(device.household_id),
        "device.error",
        {
            "device_id": str(device.id),
            "label": device.label,
            "error": error_data,
        },
    )

    logger.warning(f"Device error: {device.label} — {error_data}")


async def process_filter_alert(db: AsyncSession, device: SmartThingsDevice):
    """Generate maintenance task for filter replacement/cleaning."""
    now = datetime.now(timezone.utc)

    event = DeviceEvent(
        device_id=device.id,
        household_id=device.household_id,
        event_type=DeviceEventType.filter_alert,
        event_data={"device_label": device.label, "total_cycles": device.total_cycles},
    )
    db.add(event)
    device.last_event_at = now

    # Generate maintenance task
    filter_tasks = {
        "dryer": "Pluizenfilter van de droger schoonmaken",
        "robot_vacuum": "Filter van de robotstofzuiger vervangen",
        "air_purifier": "Filter van de luchtreiniger vervangen",
        "dishwasher": "Filter van de vaatwasser schoonmaken",
    }
    task_title = filter_tasks.get(device.device_type.value, f"Filter van {device.label} controleren")

    # Check if similar task already exists
    existing = await db.execute(
        select(Task).where(
            Task.household_id == device.household_id,
            Task.title == task_title,
            Task.status.in_(["open", "in_progress"]),
        )
    )
    if not existing.scalar_one_or_none():
        task = Task(
            household_id=device.household_id,
            title=task_title,
            description=f"Automatisch gedetecteerd door {device.label} na {device.total_cycles} cycli.",
            category="household",
            task_type="quick",
            estimated_minutes=10,
            ai_generated=True,
        )
        db.add(task)

    await db.commit()
    logger.info(f"Filter alert: {device.label} (household {device.household_id})")
