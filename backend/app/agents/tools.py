"""
Explicit tool system.

The LLM can only ever request ONE of these named tools with validated
arguments. There is no generic "execute code" or "run query" tool, and
none of these tools can move money — that only happens via the
checkout/payments API after the Policy Engine has ruled on the intent.
"""
from sqlalchemy.orm import Session

from app.models.product import Product


def search_products(db: Session, merchant_id: str, *, category: str | None = None,
                     max_price: float | None = None, tags: list[str] | None = None,
                     query_text: str | None = None, limit: int = 10) -> list[dict]:
    """Search the merchant's catalog. Never returns the raw DB — only AI-safe fields."""
    q = db.query(Product).filter(Product.merchant_id == merchant_id)
    if category:
        q = q.filter(Product.category.ilike(f"%{category}%"))
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    results = q.limit(200).all()

    if tags:
        wanted = {t.lower() for t in tags}
        results = [p for p in results if wanted & {t.lower() for t in (p.tags or [])}]

    if query_text:
        needle = query_text.lower()
        results = [
            p for p in results
            if needle in (p.name or "").lower() or needle in (p.description or "").lower()
        ]

    return [p.to_ai_context() for p in results[:limit]]


def get_product(db: Session, merchant_id: str, product_id: str) -> dict | None:
    p = db.query(Product).filter(Product.merchant_id == merchant_id, Product.id == product_id).first()
    return p.to_ai_context() if p else None


def compare_products(db: Session, merchant_id: str, product_ids: list[str]) -> list[dict]:
    products = (
        db.query(Product)
        .filter(Product.merchant_id == merchant_id, Product.id.in_(product_ids))
        .all()
    )
    return [p.to_ai_context() for p in products]


def check_inventory(db: Session, merchant_id: str, product_id: str) -> dict:
    p = db.query(Product).filter(Product.merchant_id == merchant_id, Product.id == product_id).first()
    if not p:
        return {"product_id": product_id, "exists": False, "in_stock": False, "inventory": 0}
    return {"product_id": product_id, "exists": True, "in_stock": p.inventory > 0, "inventory": p.inventory}


def calculate_cart(db: Session, merchant_id: str, line_items: list[dict]) -> dict:
    """
    line_items: [{"product_id": ..., "qty": 1}, ...]
    Re-prices every line item server-side from the DB — the AI's stated
    prices are never trusted for the actual total.
    """
    resolved = []
    subtotal = 0.0
    for item in line_items:
        p = db.query(Product).filter(
            Product.merchant_id == merchant_id, Product.id == item["product_id"]
        ).first()
        if not p:
            continue
        qty = max(1, int(item.get("qty", 1)))
        line_total = p.price * qty
        subtotal += line_total
        resolved.append({
            "product_id": p.id,
            "name": p.name,
            "unit_price": p.price,
            "qty": qty,
            "line_total": line_total,
        })
    return {"line_items": resolved, "subtotal": round(subtotal, 2), "currency": "INR"}


def get_upsell_candidates(db: Session, merchant_id: str, product_id: str) -> list[dict]:
    p = db.query(Product).filter(Product.merchant_id == merchant_id, Product.id == product_id).first()
    if not p or not p.upsell_product_ids:
        return []
    candidates = (
        db.query(Product)
        .filter(Product.merchant_id == merchant_id, Product.id.in_(p.upsell_product_ids))
        .filter(Product.inventory > 0)
        .all()
    )
    return [c.to_ai_context() for c in candidates]


def get_cross_sell_candidates(db: Session, merchant_id: str, product_id: str) -> list[dict]:
    p = db.query(Product).filter(Product.merchant_id == merchant_id, Product.id == product_id).first()
    if not p or not p.cross_sell_product_ids:
        return []
    candidates = (
        db.query(Product)
        .filter(Product.merchant_id == merchant_id, Product.id.in_(p.cross_sell_product_ids))
        .filter(Product.inventory > 0)
        .all()
    )
    return [c.to_ai_context() for c in candidates]


# Registry the agent orchestrator dispatches against — nothing outside this dict is callable.
TOOL_REGISTRY = {
    "search_products": search_products,
    "get_product": get_product,
    "compare_products": compare_products,
    "check_inventory": check_inventory,
    "calculate_cart": calculate_cart,
    "get_upsell_candidates": get_upsell_candidates,
    "get_cross_sell_candidates": get_cross_sell_candidates,
}
