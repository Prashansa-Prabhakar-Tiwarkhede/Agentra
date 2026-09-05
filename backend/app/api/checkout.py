import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents import tools
from app.audit.logger import log_event
from app.database import get_db
from app.models.merchant import Merchant
from app.models.order import CheckoutIntent
from app.policies.engine import evaluate_transaction, PolicyDecision
from app.schemas.commerce import (
    CreateCheckoutIntentRequest, CheckoutIntentOut, ApproveCheckoutRequest,
)

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/intent", response_model=CheckoutIntentOut)
def create_checkout_intent(payload: CreateCheckoutIntentRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == payload.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    # Re-price server-side. The AI's/frontend's stated prices are never trusted.
    cart = tools.calculate_cart(
        db, merchant.id, [item.model_dump() for item in payload.line_items]
    )
    if not cart["line_items"]:
        raise HTTPException(status_code=400, detail="No valid products in cart")

    subtotal = cart["subtotal"]
    discount_amount = subtotal * (payload.discount_percent / 100)
    total = round(subtotal - discount_amount, 2)

    idempotency_key = str(uuid.uuid4())
    intent = CheckoutIntent(
        merchant_id=merchant.id,
        session_id=payload.session_id,
        line_items=cart["line_items"],
        subtotal=subtotal,
        total=total,
        currency=cart["currency"],
        idempotency_key=idempotency_key,
    )
    db.add(intent)
    db.flush()

    result = evaluate_transaction(
        policy=merchant.policy,
        total_amount=total,
        buyer_budget=payload.buyer_budget,
        discount_percent=payload.discount_percent,
    )

    intent.policy_decision = result.decision.value
    intent.policy_reason = result.reason
    intent.requires_approval = result.decision == PolicyDecision.REQUIRES_APPROVAL
    intent.buyer_approved = True if result.decision == PolicyDecision.ALLOWED else None
    db.commit()
    db.refresh(intent)

    log_event(
        db, merchant_id=merchant.id, session_id=payload.session_id, event_type="POLICY_CHECK",
        actor="system", input_data={"total": total, "checks": result.checks},
        policy_decision=result.decision.value, amount=total, result="success", reason=result.reason,
    )

    if intent.requires_approval:
        log_event(
            db, merchant_id=merchant.id, session_id=payload.session_id,
            event_type="BUYER_APPROVAL_REQUESTED", actor="system",
            reason=result.reason, amount=total, result="pending",
        )

    return intent


@router.post("/approve", response_model=CheckoutIntentOut)
def approve_checkout(payload: ApproveCheckoutRequest, db: Session = Depends(get_db)):
    intent = db.query(CheckoutIntent).filter(CheckoutIntent.id == payload.checkout_intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Checkout intent not found")
    if intent.policy_decision == PolicyDecision.BLOCKED.value:
        raise HTTPException(status_code=400, detail="This transaction was blocked and cannot be approved")

    merchant = db.query(Merchant).filter(Merchant.id == intent.merchant_id).first()

    if not payload.approve:
        intent.buyer_approved = False
        intent.status = "cancelled"
        db.commit()
        log_event(
            db, merchant_id=intent.merchant_id, session_id=intent.session_id,
            event_type="BUYER_REJECTED", actor="buyer", amount=intent.total, result="cancelled",
        )
        db.refresh(intent)
        return intent

    # Re-run the policy engine with approval flag set — this is the only way
    # a REQUIRES_APPROVAL transaction can become ALLOWED.
    result = evaluate_transaction(
        policy=merchant.policy, total_amount=intent.total, already_buyer_approved=True,
    )
    intent.buyer_approved = True
    intent.policy_decision = result.decision.value
    intent.policy_reason = result.reason
    intent.status = "approved"
    db.commit()
    db.refresh(intent)

    log_event(
        db, merchant_id=intent.merchant_id, session_id=intent.session_id,
        event_type="BUYER_APPROVED", actor="buyer", amount=intent.total,
        policy_decision=result.decision.value, result="success",
    )
    return intent


@router.get("/intent/{intent_id}", response_model=CheckoutIntentOut)
def get_checkout_intent(intent_id: str, db: Session = Depends(get_db)):
    intent = db.query(CheckoutIntent).filter(CheckoutIntent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Checkout intent not found")
    return intent
