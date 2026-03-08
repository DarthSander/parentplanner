"""
Picknick integration router.

All endpoints require the "picknick" feature (family tier only).
Authentication: stored encrypted email/password, no OAuth2.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_member
from core.rate_limiter import limiter
from core.subscription_guard import require_feature
from models.picknick import PicknickListStatus, PicknickShoppingList
from schemas.picknick import (
    PicknickConnectRequest,
    PicknickListItemCreate,
    PicknickListItemUpdate,
    PicknickOrderResponse,
    PicknickProductResponse,
    PicknickRecommendationsResponse,
    PicknickShoppingListCreate,
    PicknickShoppingListDetailResponse,
    PicknickShoppingListResponse,
    PicknickStatusResponse,
    SendToPicknickResponse,
)
from services.picknick.auth import (
    connect_picknick,
    disconnect_picknick,
    get_integration,
    get_picknick_client_for_integration,
)
from services.picknick.products import (
    get_order_history,
    search_and_cache_products,
)
from services.picknick.recommendations import generate_shopping_recommendations
from services.picknick.shopping import (
    add_item_to_list,
    get_or_create_active_list,
    mark_list_delivered,
    send_list_to_picknick,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helper ────────────────────────────────────────────────────────────────────

async def _require_integration(db: AsyncSession, household_id: UUID):
    """Get integration or raise 404."""
    integration = await get_integration(db, household_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail={"code": "PICKNICK_NOT_CONNECTED", "message": "Geen Picknick-account gekoppeld. Koppel eerst je account via Instellingen."},
        )
    return integration


# ── Connect / Status / Disconnect ─────────────────────────────────────────────

@router.post("/connect", status_code=201)
async def connect(
    payload: PicknickConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Connect a Picknick account (email + password). Validates credentials live."""
    try:
        integration = await connect_picknick(
            db=db,
            household_id=current_member.household_id,
            member_id=current_member.id,
            email=payload.email,
            password=payload.password,
            country_code=payload.country_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_CREDENTIALS", "message": str(e)})
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={"code": "LIBRARY_ERROR", "message": str(e)})
    return {"message": "Picknick-account succesvol gekoppeld.", "integration_id": str(integration.id)}


@router.get("/status", response_model=PicknickStatusResponse)
async def status(
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    integration = await get_integration(db, current_member.household_id)
    if not integration:
        return PicknickStatusResponse(connected=False)

    from models.picknick import PicknickShoppingList
    count = await db.scalar(
        select(PicknickShoppingList).where(
            PicknickShoppingList.household_id == current_member.household_id
        )
    )
    return PicknickStatusResponse(
        connected=True,
        country_code=integration.country_code,
        last_synced_at=integration.last_synced_at,
        list_count=count or 0,
        integration_id=integration.id,
    )


@router.delete("/disconnect", status_code=204)
async def disconnect(
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    integration = await _require_integration(db, current_member.household_id)
    await disconnect_picknick(db, integration)


# ── Product Search ─────────────────────────────────────────────────────────────

@router.get("/products/search", response_model=list[PicknickProductResponse])
@limiter.limit("30/minute")
async def search_products(
    request: Request,
    q: str,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Search the Picknick catalog. Results are cached for 24h."""
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Zoekopdracht moet minimaal 2 tekens bevatten.")

    integration = await _require_integration(db, current_member.household_id)

    try:
        client = await get_picknick_client_for_integration(integration)
        products = await search_and_cache_products(db, current_member.household_id, client, q)
    except Exception as e:
        logger.error(f"Product search error: {e}")
        raise HTTPException(status_code=502, detail={"code": "PICKNICK_API_ERROR", "message": "Picknick is tijdelijk niet bereikbaar."})

    return products


# ── Shopping Lists ─────────────────────────────────────────────────────────────

@router.get("/lists", response_model=list[PicknickShoppingListResponse])
async def list_shopping_lists(
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    integration = await _require_integration(db, current_member.household_id)
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.household_id == current_member.household_id,
            PicknickShoppingList.integration_id == integration.id,
        ).order_by(PicknickShoppingList.created_at.desc())
    )
    lists = result.scalars().all()

    response = []
    for lst in lists:
        from sqlalchemy import func
        from models.picknick import PicknickListItem
        count = await db.scalar(
            select(func.count()).where(PicknickListItem.list_id == lst.id)
        )
        response.append(PicknickShoppingListResponse(
            id=lst.id,
            household_id=lst.household_id,
            name=lst.name,
            status=lst.status if isinstance(lst.status, str) else lst.status.value,
            ai_generated=lst.ai_generated,
            notes=lst.notes,
            item_count=count or 0,
            sent_at=lst.sent_at,
            delivered_at=lst.delivered_at,
            created_at=lst.created_at,
            updated_at=lst.updated_at,
        ))
    return response


@router.post("/lists", response_model=PicknickShoppingListResponse, status_code=201)
async def create_shopping_list(
    payload: PicknickShoppingListCreate,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    integration = await _require_integration(db, current_member.household_id)
    lst = await get_or_create_active_list(
        db, current_member.household_id, integration.id,
        created_by=current_member.id, name=payload.name,
    )
    return PicknickShoppingListResponse(
        id=lst.id, household_id=lst.household_id, name=lst.name,
        status=lst.status if isinstance(lst.status, str) else lst.status.value,
        ai_generated=lst.ai_generated, notes=lst.notes, item_count=0,
        sent_at=lst.sent_at, delivered_at=lst.delivered_at,
        created_at=lst.created_at, updated_at=lst.updated_at,
    )


@router.get("/lists/{list_id}", response_model=PicknickShoppingListDetailResponse)
async def get_shopping_list(
    list_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.id == list_id,
            PicknickShoppingList.household_id == current_member.household_id,
        )
    )
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=404, detail="Lijst niet gevonden.")

    from models.picknick import PicknickListItem
    items_result = await db.execute(
        select(PicknickListItem).where(PicknickListItem.list_id == list_id)
    )
    items = items_result.scalars().all()

    return PicknickShoppingListDetailResponse(
        id=lst.id, household_id=lst.household_id, name=lst.name,
        status=lst.status if isinstance(lst.status, str) else lst.status.value,
        ai_generated=lst.ai_generated, notes=lst.notes,
        item_count=len(items), sent_at=lst.sent_at, delivered_at=lst.delivered_at,
        created_at=lst.created_at, updated_at=lst.updated_at,
        items=items,
    )


@router.delete("/lists/{list_id}", status_code=204)
async def delete_shopping_list(
    list_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.id == list_id,
            PicknickShoppingList.household_id == current_member.household_id,
        )
    )
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=404, detail="Lijst niet gevonden.")
    await db.delete(lst)
    await db.commit()


# ── List Items ─────────────────────────────────────────────────────────────────

@router.post("/lists/{list_id}/items", status_code=201)
async def add_item(
    list_id: UUID,
    payload: PicknickListItemCreate,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.id == list_id,
            PicknickShoppingList.household_id == current_member.household_id,
        )
    )
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=404, detail="Lijst niet gevonden.")

    item = await add_item_to_list(
        db, lst,
        name=payload.name,
        quantity=payload.quantity,
        unit=payload.unit,
        picknick_product_id=payload.picknick_product_id,
        inventory_item_id=payload.inventory_item_id,
        added_by=current_member.id,
    )
    return item


@router.patch("/lists/{list_id}/items/{item_id}")
async def update_item(
    list_id: UUID,
    item_id: UUID,
    payload: PicknickListItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    from models.picknick import PicknickListItem
    result = await db.execute(
        select(PicknickListItem).where(
            PicknickListItem.id == item_id,
            PicknickListItem.list_id == list_id,
            PicknickListItem.household_id == current_member.household_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item niet gevonden.")

    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.checked is not None:
        item.checked = payload.checked
    if payload.picknick_product_id is not None:
        item.picknick_product_id = payload.picknick_product_id

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/lists/{list_id}/items/{item_id}", status_code=204)
async def delete_item(
    list_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    from models.picknick import PicknickListItem
    result = await db.execute(
        select(PicknickListItem).where(
            PicknickListItem.id == item_id,
            PicknickListItem.list_id == list_id,
            PicknickListItem.household_id == current_member.household_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item niet gevonden.")
    await db.delete(item)
    await db.commit()


# ── Send to Picknick ──────────────────────────────────────────────────────────

@router.post("/lists/{list_id}/send", response_model=SendToPicknickResponse)
@limiter.limit("10/minute")
async def send_list(
    request: Request,
    list_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Push the list to the Picknick shopping cart in one click."""
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.id == list_id,
            PicknickShoppingList.household_id == current_member.household_id,
        )
    )
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=404, detail="Lijst niet gevonden.")

    integration = await _require_integration(db, current_member.household_id)

    try:
        client = await get_picknick_client_for_integration(integration)
        summary = await send_list_to_picknick(db, client, lst)
    except Exception as e:
        logger.error(f"Send to Picknick failed: {e}")
        raise HTTPException(status_code=502, detail={"code": "PICKNICK_API_ERROR", "message": "Picknick is tijdelijk niet bereikbaar."})

    return SendToPicknickResponse(**summary)


@router.post("/lists/{list_id}/delivered", status_code=200)
async def mark_delivered(
    list_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Mark a sent list as delivered → auto-updates linked inventory quantities."""
    result = await db.execute(
        select(PicknickShoppingList).where(
            PicknickShoppingList.id == list_id,
            PicknickShoppingList.household_id == current_member.household_id,
        )
    )
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=404, detail="Lijst niet gevonden.")

    await mark_list_delivered(db, lst)
    return {"message": "Bestelling gemarkeerd als bezorgd. Voorraad bijgewerkt."}


# ── Recommendations ────────────────────────────────────────────────────────────

@router.get("/recommendations", response_model=PicknickRecommendationsResponse)
@limiter.limit("10/minute")
async def get_recommendations(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """AI-generated shopping recommendations based on inventory, calendar, SmartThings, and patterns."""
    await _require_integration(db, current_member.household_id)

    items, context_summary = await generate_shopping_recommendations(db, current_member.household_id)
    return PicknickRecommendationsResponse(
        items=items,
        generated_at=datetime.now(timezone.utc),
        context_summary=context_summary,
    )


@router.post("/recommendations/add-to-list", status_code=201)
async def add_recommendations_to_list(
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Generate recommendations and add them all to the active shopping list."""
    integration = await _require_integration(db, current_member.household_id)

    items, _ = await generate_shopping_recommendations(db, current_member.household_id)
    if not items:
        return {"message": "Geen aanbevelingen gevonden.", "items_added": 0}

    lst = await get_or_create_active_list(
        db, current_member.household_id, integration.id,
        name="AI Boodschappenlijst",
    )

    added = 0
    for item in items:
        await add_item_to_list(
            db, lst,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            picknick_product_id=item.picknick_product_id,
            inventory_item_id=item.inventory_item_id,
            ai_suggested=True,
            ai_reason=item.reason,
        )
        added += 1

    lst.ai_generated = True
    await db.commit()

    return {"message": f"{added} aanbeveling(en) toegevoegd aan de boodschappenlijst.", "items_added": added, "list_id": str(lst.id)}


# ── Order History ─────────────────────────────────────────────────────────────

@router.get("/orders", response_model=list[PicknickOrderResponse])
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Fetch cached Picknick order history."""
    from models.picknick import PicknickOrderHistory
    result = await db.execute(
        select(PicknickOrderHistory).where(
            PicknickOrderHistory.household_id == current_member.household_id,
        ).order_by(PicknickOrderHistory.order_date.desc()).limit(20)
    )
    orders = result.scalars().all()
    return [
        PicknickOrderResponse(
            id=o.id,
            picknick_order_id=o.picknick_order_id,
            order_date=o.order_date,
            delivery_date=o.delivery_date,
            total_price=float(o.total_price) if o.total_price else None,
            status=o.status,
            item_count=len(o.items_json.get("items", [])) if o.items_json else 0,
            created_at=o.created_at,
        )
        for o in orders
    ]


@router.post("/sync", status_code=200)
@limiter.limit("5/hour")
async def manual_sync(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    _tier: str = Depends(require_feature("picknick")),
):
    """Manually trigger order history sync from Picknick."""
    integration = await _require_integration(db, current_member.household_id)

    try:
        client = await get_picknick_client_for_integration(integration)
        raw_orders = await get_order_history(client)
    except Exception as e:
        raise HTTPException(status_code=502, detail={"code": "PICKNICK_API_ERROR", "message": str(e)})

    from models.picknick import PicknickOrderHistory
    synced = 0
    for raw in raw_orders:
        order_id = str(raw.get("id", ""))
        if not order_id:
            continue

        existing = await db.execute(
            select(PicknickOrderHistory).where(PicknickOrderHistory.picknick_order_id == order_id)
        )
        if existing.scalar_one_or_none():
            continue

        db.add(PicknickOrderHistory(
            household_id=current_member.household_id,
            integration_id=integration.id,
            picknick_order_id=order_id,
            items_json=raw,
        ))
        synced += 1

    integration.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": f"Sync afgerond. {synced} nieuwe orders opgeslagen."}
