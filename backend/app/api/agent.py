from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.rate_limit import limiter
from app.models.merchant import Merchant
from app.schemas.commerce import ChatRequest, ChatResponse
from app.agents.agent import run_buyer_turn

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat(request: Request, payload: ChatRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == payload.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    result = run_buyer_turn(
        db,
        merchant=merchant,
        session_id=payload.session_id,
        message=payload.message,
        buyer_budget_override=payload.buyer_budget,
    )
    return result
