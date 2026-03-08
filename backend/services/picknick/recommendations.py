"""
AI-powered shopping recommendation engine.

Combines signals from:
 - Inventory levels (below threshold)
 - SmartThings appliance cycles (e.g. dishwasher ran 5x → check detergent)
 - Calendar events (opvangdag → luiers, voeding)
 - Picknick order history patterns (weekly milk purchase)
 - Pattern engine data (inventory_rate, shopping_frequency)

Returns a prioritized list of RecommendedItems.
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.picknick import PicknickRecommendedItem
from services.ai.ai_utils import AICallError, call_claude, parse_json_response
from services.vector.retrieval import retrieve_context

logger = logging.getLogger(__name__)


async def generate_shopping_recommendations(
    db: AsyncSession,
    household_id: UUID,
) -> tuple[list[PicknickRecommendedItem], str]:
    """
    Generate AI-powered shopping recommendations.
    Returns (items, context_summary).
    """
    context_parts = []

    # ── 1. Inventory below threshold ─────────────────────────────────────────
    low_stock_lines = await _get_low_stock_summary(db, household_id)
    if low_stock_lines:
        context_parts.append("LAGE VOORRAAD:\n" + "\n".join(low_stock_lines))

    # ── 2. Calendar events (next 48 hours) ───────────────────────────────────
    calendar_lines = await _get_calendar_context(db, household_id)
    if calendar_lines:
        context_parts.append("AGENDA KOMENDE 48 UUR:\n" + "\n".join(calendar_lines))

    # ── 3. SmartThings — consumables near depletion ───────────────────────────
    appliance_lines = await _get_smartthings_consumables(db, household_id)
    if appliance_lines:
        context_parts.append("SMARTTHINGS VERBRUIKSARTIKELEN:\n" + "\n".join(appliance_lines))

    # ── 4. Order history patterns ─────────────────────────────────────────────
    history_lines = await _get_order_history_summary(db, household_id)
    if history_lines:
        context_parts.append("AANKOOPPATRONEN (recente orders):\n" + "\n".join(history_lines))

    # ── 5. Vector context ─────────────────────────────────────────────────────
    vector_context = await retrieve_context(
        db, household_id, "boodschappen voorraad aankopen producten", top_k=8
    )
    if vector_context:
        context_parts.append("RELEVANTE CONTEXT:\n" + "\n".join(vector_context[:6]))

    full_context = "\n\n".join(context_parts) if context_parts else "Geen specifieke context beschikbaar."

    system_prompt = """
Je bent de slimme boodschappenassistent van GezinsAI. Analyseer de context en genereer een geprioriteerde boodschappenlijst.

INSTRUCTIES:
- Prioriteit "urgent": voorraad kritiek laag of opvangdag morgen
- Prioriteit "normal": regelmatig benodigde items, laag maar niet kritiek
- Prioriteit "suggestion": handig om te hebben op basis van patronen
- Bron: "inventory_low" | "calendar" | "smartthings" | "pattern"
- Wees specifiek (aantal/hoeveelheid)
- Maximaal 15 items
- Geef een korte reden per item

Antwoord met ALLEEN een JSON array:
[
  {
    "name": "Pampers luiers maat 4",
    "quantity": 2,
    "unit": "pakken",
    "reason": "Nog maar 3 luiers op voorraad, opvangdag morgen",
    "priority": "urgent",
    "source": "inventory_low"
  }
]
"""

    try:
        response = await call_claude(
            system=system_prompt,
            user_message=f"Datum: {datetime.now(timezone.utc).strftime('%A %d %B %Y')}.\n\n{full_context}",
            max_tokens=1500,
        )
        raw = parse_json_response(response)
        items = []
        for item_dict in (raw if isinstance(raw, list) else [raw]):
            try:
                items.append(PicknickRecommendedItem(**item_dict))
            except Exception as e:
                logger.warning(f"Skipping invalid recommendation item: {e}")
    except AICallError as e:
        logger.error(f"Recommendation generation failed for {household_id}: {e}")
        items = _fallback_recommendations(low_stock_lines)

    # Build context summary for UI
    summary_parts = []
    if low_stock_lines:
        summary_parts.append(f"{len(low_stock_lines)} item(s) bijna op")
    if calendar_lines:
        summary_parts.append("agenda-events morgen")
    if appliance_lines:
        summary_parts.append("verbruiksartikelen apparaten")
    context_summary = ", ".join(summary_parts) if summary_parts else "Basisaanbevelingen"

    return items, context_summary


# ── Context builders ──────────────────────────────────────────────────────────

async def _get_low_stock_summary(db: AsyncSession, household_id: UUID) -> list[str]:
    from models.inventory import InventoryItem
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.household_id == household_id,
            InventoryItem.current_quantity <= InventoryItem.threshold_quantity,
        )
    )
    items = result.scalars().all()
    lines = []
    for item in items:
        lines.append(
            f"- {item.name}: nog {float(item.current_quantity)} {item.unit} "
            f"(drempel: {float(item.threshold_quantity)} {item.unit})"
        )
    return lines


async def _get_calendar_context(db: AsyncSession, household_id: UUID) -> list[str]:
    try:
        from models.calendar import CalendarEvent
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.household_id == household_id,
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= now + timedelta(hours=48),
            )
        )
        events = result.scalars().all()
        return [
            f"- {event.title} op {event.start_time.strftime('%A %d %B om %H:%M')}"
            for event in events
        ]
    except Exception:
        return []


async def _get_smartthings_consumables(db: AsyncSession, household_id: UUID) -> list[str]:
    """Return consumables that are within 5 cycles of running out."""
    try:
        from models.inventory import InventoryItem
        from models.smartthings import DeviceConsumable, SmartThingsDevice

        devices_result = await db.execute(
            select(SmartThingsDevice).where(SmartThingsDevice.household_id == household_id)
        )
        devices = devices_result.scalars().all()
        lines = []

        for device in devices:
            consumables_result = await db.execute(
                select(DeviceConsumable).where(DeviceConsumable.device_id == device.id)
            )
            for consumable in consumables_result.scalars():
                inv_result = await db.execute(
                    select(InventoryItem).where(InventoryItem.id == consumable.inventory_item_id)
                )
                inv_item = inv_result.scalar_one_or_none()
                if inv_item and consumable.usage_per_cycle:
                    cycles_left = float(inv_item.current_quantity) / float(consumable.usage_per_cycle)
                    if cycles_left <= 5:
                        lines.append(
                            f"- {inv_item.name}: ~{int(cycles_left)} beurten over "
                            f"(voor {device.label})"
                        )
        return lines
    except Exception as e:
        logger.warning(f"SmartThings consumable check failed: {e}")
        return []


async def _get_order_history_summary(db: AsyncSession, household_id: UUID) -> list[str]:
    """Summarize recent Picknick order items for pattern context."""
    try:
        from models.picknick import PicknickOrderHistory
        result = await db.execute(
            select(PicknickOrderHistory).where(
                PicknickOrderHistory.household_id == household_id,
            ).order_by(PicknickOrderHistory.order_date.desc()).limit(5)
        )
        orders = result.scalars().all()
        lines = []
        for order in orders:
            if order.items_json:
                item_names = [
                    i.get("name", "") for i in order.items_json.get("items", [])[:5]
                    if isinstance(i, dict)
                ]
                if item_names:
                    date_str = order.order_date.strftime("%d %B") if order.order_date else "?"
                    lines.append(f"- Order {date_str}: {', '.join(item_names)}")
        return lines
    except Exception:
        return []


def _fallback_recommendations(low_stock_lines: list[str]) -> list[PicknickRecommendedItem]:
    """Return simple inventory-based recommendations when AI fails."""
    items = []
    for line in low_stock_lines[:10]:
        # Parse "- Luiers: nog 3 stuks (drempel: 10 stuks)"
        name = line.strip("- ").split(":")[0].strip()
        items.append(PicknickRecommendedItem(
            name=name,
            quantity=1.0,
            unit=None,
            reason="Voorraad onder drempelwaarde",
            priority="normal",
            source="inventory_low",
        ))
    return items
