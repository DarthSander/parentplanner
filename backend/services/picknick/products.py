"""
Picknick product search and catalog caching.

Products are fetched from Picknick's API and cached locally in `picknick_products`.
Cache TTL: 24 hours (checked via last_seen_at).
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 24


async def search_products(client, query: str, max_results: int = 20) -> list[dict]:
    """
    Search Picknick for products matching `query`.
    Returns raw product dicts from the API.
    """
    try:
        results = client.search(query)
        items = []
        for item in results:
            # python-picnic-api returns list of dicts with nested structure
            if item.get("type") == "SINGLE_ARTICLE":
                items.append(item)
            elif item.get("type") == "ARTICLE_CATEGORY":
                items.extend(item.get("items", []))
        return items[:max_results]
    except Exception as e:
        logger.error(f"Picknick product search failed for '{query}': {e}")
        return []


def _parse_product(raw: dict) -> dict | None:
    """Parse a raw Picknick API product into a normalized dict."""
    try:
        price_raw = raw.get("price", 0)
        # price is in cents in the Picknick API
        price = price_raw / 100 if isinstance(price_raw, int) else price_raw
        return {
            "picknick_id": raw.get("id", ""),
            "name": raw.get("name", ""),
            "category": raw.get("category", None),
            "subcategory": None,
            "price": price,
            "unit_quantity": raw.get("unit_quantity", None),
            "image_url": raw.get("image_id", None),  # Picknick uses image_id
            "available": not raw.get("max_count", 1) == 0,
        }
    except Exception as e:
        logger.warning(f"Failed to parse Picknick product: {e}")
        return None


async def search_and_cache_products(
    db: AsyncSession,
    household_id: UUID,
    client,
    query: str,
) -> list:
    """
    Search Picknick for `query`, upsert results into cache, return model instances.
    """
    from models.picknick import PicknickProduct

    raw_results = await search_products(client, query)
    products = []

    for raw in raw_results:
        parsed = _parse_product(raw)
        if not parsed or not parsed["picknick_id"]:
            continue

        # Upsert into cache
        result = await db.execute(
            select(PicknickProduct).where(
                PicknickProduct.household_id == household_id,
                PicknickProduct.picknick_id == parsed["picknick_id"],
            )
        )
        product = result.scalar_one_or_none()

        if product:
            product.name = parsed["name"]
            product.price = parsed["price"]
            product.available = parsed["available"]
            product.last_seen_at = datetime.now(timezone.utc)
        else:
            product = PicknickProduct(
                household_id=household_id,
                **parsed,
            )
            db.add(product)

        products.append(product)

    await db.commit()
    return products


async def find_picknick_match_for_inventory_item(
    db: AsyncSession,
    household_id: UUID,
    client,
    item_name: str,
) -> list:
    """
    Find the best Picknick product matches for a local inventory item.
    First checks cache; if stale or empty, fetches from API.
    Returns up to 5 candidate PicknickProduct models.
    """
    from models.picknick import PicknickProduct

    # Check cache freshness
    cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)
    result = await db.execute(
        select(PicknickProduct).where(
            PicknickProduct.household_id == household_id,
            PicknickProduct.name.ilike(f"%{item_name}%"),
            PicknickProduct.last_seen_at >= cutoff,
        ).limit(5)
    )
    cached = result.scalars().all()

    if cached:
        return cached

    # Cache miss or stale — search from API
    return await search_and_cache_products(db, household_id, client, item_name)


async def get_order_history(client) -> list[dict]:
    """Fetch recent orders from Picknick API."""
    try:
        orders = client.get_orders()
        return orders if isinstance(orders, list) else []
    except Exception as e:
        logger.error(f"Picknick order history fetch failed: {e}")
        return []
