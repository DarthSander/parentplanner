from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from models.inventory import InventoryAlert, InventoryItem
from models.member import Member, MemberRole
from schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate, LowStockReport

router = APIRouter()


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: InventoryCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Zorgverleners kunnen geen voorraad aanmaken.")

    item = InventoryItem(
        household_id=member.household_id,
        name=payload.name,
        category=payload.category,
        current_quantity=payload.current_quantity,
        unit=payload.unit,
        threshold_quantity=payload.threshold_quantity,
        preferred_store_url=payload.preferred_store_url,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("", response_model=list[InventoryResponse])
async def list_items(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.household_id == member.household_id)
            .order_by(InventoryItem.name)
    )
    return result.scalars().all()


@router.patch("/{item_id}", response_model=InventoryResponse)
async def update_item(
    item_id: UUID,
    payload: InventoryUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Zorgverleners kunnen geen voorraad aanpassen.")

    result = await db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.household_id == member.household_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.household_id == member.household_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(item)
    await db.commit()


@router.post("/{item_id}/report-low", status_code=status.HTTP_201_CREATED)
async def report_low_stock(
    item_id: UUID,
    payload: LowStockReport,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Report low stock — available to all roles including caregiver."""
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.household_id == member.household_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    alert = InventoryAlert(
        item_id=item.id,
        household_id=member.household_id,
        reported_by=member.id,
        alert_type="caregiver_report",
        message=payload.message,
    )
    db.add(alert)
    await db.commit()
    return {"message": "Melding verstuurd."}


@router.post("/{item_id}/restock", response_model=InventoryResponse)
async def restock_item(
    item_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.role == MemberRole.caregiver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.household_id == member.household_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    item.current_quantity = item.threshold_quantity * 2
    item.last_restocked_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)

    # Resolve open alerts
    alerts_result = await db.execute(
        select(InventoryAlert).where(InventoryAlert.item_id == item.id, InventoryAlert.resolved == False)
    )
    for alert in alerts_result.scalars():
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)
    return item
