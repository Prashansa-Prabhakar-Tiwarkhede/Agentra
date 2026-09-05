from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.auth import get_current_merchant
from app.database import get_db
from app.models.merchant import Merchant
from app.models.order import Order
from app.models.session import AgentSession
from app.models.audit import AuditEvent

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.merchant_id == merchant.id).all()
    paid_orders = [o for o in orders if o.payment_status == "paid"]
    failed_orders = [o for o in orders if o.payment_status == "failed"]

    total_sessions = db.query(func.count(AgentSession.id)).filter(AgentSession.merchant_id == merchant.id).scalar() or 0
    upsell_suggested = (
        db.query(func.count(AuditEvent.id))
        .filter(AuditEvent.merchant_id == merchant.id, AuditEvent.event_type == "UPSELL_SUGGESTED")
        .scalar() or 0
    )
    cross_sell_suggested = (
        db.query(func.count(AuditEvent.id))
        .filter(AuditEvent.merchant_id == merchant.id, AuditEvent.event_type == "CROSS_SELL_SUGGESTED")
        .scalar() or 0
    )

    ai_gmv = sum(o.amount for o in paid_orders)
    conversion_rate = round((len(paid_orders) / total_sessions) * 100, 2) if total_sessions else 0.0
    aov = round(ai_gmv / len(paid_orders), 2) if paid_orders else 0.0

    return {
        "ai_gmv": round(ai_gmv, 2),
        "ai_orders": len(paid_orders),
        "conversion_rate_percent": conversion_rate,
        "average_order_value": aov,
        "agent_sessions": total_sessions,
        "upsells_suggested": upsell_suggested,
        "cross_sells_suggested": cross_sell_suggested,
        "successful_payments": len(paid_orders),
        "failed_payments": len(failed_orders),
        "note": "Metrics reflect this merchant's live data; seed/demo mode data is clearly labeled separately.",
    }


@router.get("/revenue-timeseries")
def revenue_timeseries(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    """Revenue and order count grouped by day, for a revenue-over-time chart.
    Computed in Python rather than a DB-specific date_trunc so it works identically
    against both SQLite (local dev) and Postgres (Supabase production)."""
    orders = (
        db.query(Order)
        .filter(Order.merchant_id == merchant.id, Order.payment_status == "paid")
        .order_by(Order.created_at.asc())
        .all()
    )
    by_day: dict[str, dict] = {}
    for o in orders:
        day_key = o.created_at.strftime("%Y-%m-%d")
        bucket = by_day.setdefault(day_key, {"date": day_key, "revenue": 0.0, "orders": 0})
        bucket["revenue"] += o.amount
        bucket["orders"] += 1
    return sorted(by_day.values(), key=lambda b: b["date"])


@router.get("/product-performance")
def product_performance(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    """Units sold and revenue per product name, from paid orders' line items."""
    orders = (
        db.query(Order)
        .filter(Order.merchant_id == merchant.id, Order.payment_status == "paid")
        .all()
    )
    by_product: dict[str, dict] = {}
    for o in orders:
        for item in (o.line_items or []):
            name = item.get("name", "Unknown")
            bucket = by_product.setdefault(name, {"name": name, "units_sold": 0, "revenue": 0.0})
            qty = item.get("qty", 1)
            bucket["units_sold"] += qty
            bucket["revenue"] += item.get("line_total", item.get("unit_price", 0) * qty)
    return sorted(by_product.values(), key=lambda b: b["revenue"], reverse=True)
