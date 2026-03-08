import logging

from core.config import settings

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI text-embedding-3-small."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
    )
    return response.data[0].embedding


def build_task_document(task, member=None) -> str:
    parts = [f"Taak: {task.title}"]
    if task.description:
        parts.append(f"Omschrijving: {task.description}")
    parts.append(f"Categorie: {task.category}")
    parts.append(f"Type: {task.task_type}")
    if member:
        parts.append(f"Toegewezen aan: {member.display_name} (rol: {member.role})")
    if task.due_date:
        parts.append(f"Deadline: {task.due_date.strftime('%A %d %B %Y')}")
    parts.append(f"Status: {task.status}")
    parts.append(f"Aantal keer uitgesteld: {task.snooze_count}")
    return ". ".join(parts)


def build_completion_document(completion, task, member) -> str:
    duration = f", duurde {completion.duration_minutes} minuten" if completion.duration_minutes else ""
    return (
        f"Taak '{task.title}' (categorie: {task.category}) afgerond door "
        f"{member.display_name} op "
        f"{completion.completed_at.strftime('%A %d %B %Y om %H:%M')}{duration}."
    )


def build_calendar_document(event, member=None) -> str:
    who = f" voor {member.display_name}" if member else ""
    return (
        f"Kalenderafspraak{who}: {event.title} op "
        f"{event.start_time.strftime('%A %d %B %Y van %H:%M')} tot "
        f"{event.end_time.strftime('%H:%M')}."
        + (f" Locatie: {event.location}." if event.location else "")
    )


def build_inventory_document(item) -> str:
    return (
        f"Voorraad: {item.name} ({item.category}). "
        f"Huidige hoeveelheid: {item.current_quantity} {item.unit}. "
        f"Drempelwaarde: {item.threshold_quantity} {item.unit}. "
        + (
            f"Gemiddeld verbruik: {item.average_consumption_rate} {item.unit} per dag."
            if item.average_consumption_rate
            else ""
        )
    )


def build_device_event_document(event, device) -> str:
    """Build text document for a SmartThings device event."""
    device_labels = {
        "washer": "Wasmachine",
        "dryer": "Droger",
        "dishwasher": "Vaatwasser",
        "robot_vacuum": "Robotstofzuiger",
        "refrigerator": "Koelkast",
        "oven": "Oven",
        "air_purifier": "Luchtreiniger",
    }
    device_label = device_labels.get(device.device_type.value if hasattr(device.device_type, 'value') else device.device_type, device.label)

    event_labels = {
        "cycle_started": "cyclus gestart",
        "cycle_completed": "cyclus afgerond",
        "door_opened": "deur geopend",
        "door_closed": "deur gesloten",
        "error": "fout opgetreden",
        "filter_alert": "filter melding",
    }
    event_label = event_labels.get(event.event_type.value if hasattr(event.event_type, 'value') else event.event_type, str(event.event_type))

    parts = [
        f"Apparaat: {device_label} ({device.label})",
        f"Gebeurtenis: {event_label}",
        f"Datum: {event.created_at.strftime('%A %d %B %Y om %H:%M')}",
        f"Totaal aantal cycli: {device.total_cycles}",
    ]

    if event.event_data:
        duration = event.event_data.get("duration_minutes")
        if duration:
            parts.append(f"Duur: {duration} minuten")

    return ". ".join(parts)
