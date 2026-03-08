"""
Shopping list service — create, manage, and send lists to Picknick.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.picknick import (
    PicknickListItem,
    PicknickListStatus,
    PicknickShoppingList,
)

logger = logging.getLogger(__name__)


async def get_active_list(db: AsyncSession, household_id: UUID, integration_id: UUID):
    """Return the current open shopping list, or None."""
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.household_id == household_id,
            PicknickShoppingList.integration_id == integration_id,
            PicknickShoppingList.status == PicknickListStatus.open,
        ).order_by(PicknickShoppingList.created_at.desc())
    )
    return result.scalar_one_or_none()


async def get_or_create_active_list(
    db: AsyncSession,
    household_id: UUID,
    integration_id: UUID,
    created_by: UUID | None = None,
    name: str = "Boodschappenlijst",
) -> PicknickShoppingList:
    """Return the current open list, or create a new one."""
    existing = await get_active_list(db, household_id, integration_id)
    if existing:
        return existing

    new_list = PicknickShoppingList(
        household_id=household_id,
        integration_id=integration_id,
        created_by=created_by,
        name=name,
    )
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    return new_list


async def add_item_to_list(
    db: AsyncSession,
    shopping_list: PicknickShoppingList,
    name: str,
    quantity: float = 1.0,
    unit: str | None = None,
    picknick_product_id: UUID | None = None,
    inventory_item_id: UUID | None = None,
    ai_suggested: bool = False,
    ai_reason: str | None = None,
    added_by: UUID | None = None,
) -> PicknickListItem:
    item = PicknickListItem(
        list_id=shopping_list.id,
        household_id=shopping_list.household_id,
        picknick_product_id=picknick_product_id,
        inventory_item_id=inventory_item_id,
        name=name,
        quantity=quantity,
        unit=unit,
        ai_suggested=ai_suggested,
        ai_reason=ai_reason,
        added_by=added_by,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def send_list_to_picknick(
    db: AsyncSession,
    client,
    shopping_list: PicknickShoppingList,
) -> dict:
    """
    Push all unchecked items in the list to the Picknick cart.
    Returns a summary: items_sent, items_failed.
    Items without a linked Picknick product ID are skipped (counted as failed).
    """
    result = await db.execute(
        select(PicknickListItem).where(
            PicknickListItem.list_id == shopping_list.id,
            PicknickListItem.checked == False,
        )
    )
    items = result.scalars().all()

    sent = 0
    failed = 0
    skipped = []

    for item in items:
        # We need the Picknick product ID to add to cart
        picknick_id = None
        if item.picknick_product_id:
            from models.picknick import PicknickProduct
            product_result = await db.execute(
                select(PicknickProduct).where(PicknickProduct.id == item.picknick_product_id)
            )
            product = product_result.scalar_one_or_none()
            if product:
                picknick_id = product.picknick_id

        if not picknick_id:
            skipped.append(item.name)
            failed += 1
            continue

        try:
            count = max(1, int(item.quantity))
            client.add_product_to_cart(picknick_id, count)
            sent += 1
        except Exception as e:
            logger.error(f"Failed to add '{item.name}' to Picknick cart: {e}")
            failed += 1

    # Update list status
    shopping_list.status = PicknickListStatus.sent_to_picknick
    shopping_list.sent_at = datetime.now(timezone.utc)
    await db.commit()

    msg_parts = [f"{sent} item(s) naar Picknick gestuurd."]
    if failed:
        msg_parts.append(
            f"{failed} item(s) konden niet worden toegevoegd (geen Picknick-product gekoppeld)."
        )
    if skipped:
        msg_parts.append(f"Overgeslagen: {', '.join(skipped[:5])}.")

    return {
        "success": sent > 0,
        "items_sent": sent,
        "items_failed": failed,
        "message": " ".join(msg_parts),
    }


async def mark_list_delivered(
    db: AsyncSession,
    shopping_list: PicknickShoppingList,
) -> None:
    """
    Mark a list as delivered and update inventory quantities for linked items.
    """
    from models.inventory import InventoryItem
    from datetime import datetime, timezone

    result = await db.execute(
        select(PicknickListItem).where(PicknickListItem.list_id == shopping_list.id)
    )
    items = result.scalars().all()

    for item in items:
        if item.inventory_item_id:
            inv_result = await db.execute(
                select(InventoryItem).where(InventoryItem.id == item.inventory_item_id)
            )
            inv_item = inv_result.scalar_one_or_none()
            if inv_item:
                inv_item.current_quantity = float(inv_item.current_quantity) + float(item.quantity)
                inv_item.last_restocked_at = datetime.now(timezone.utc)

    shopping_list.status = PicknickListStatus.delivered
    shopping_list.delivered_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info(f"Shopping list {shopping_list.id} marked as delivered, inventory updated.")
