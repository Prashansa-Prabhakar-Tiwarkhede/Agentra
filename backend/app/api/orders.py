from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_merchant
from app.database import get_db
from app.models.merchant import Merchant
from app.models.order import Order
from app.schemas.commerce import OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    return (
        db.query(Order)
        .filter(Order.merchant_id == merchant.id)
        .order_by(Order.created_at.desc())
        .all()
    )
