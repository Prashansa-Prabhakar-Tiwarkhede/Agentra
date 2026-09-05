import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.config import get_settings
from app.database import get_db
from app.rate_limit import limiter
from app.models.merchant import Merchant
from app.models.order import CheckoutIntent, Order
from app.models.payment import PaymentAttempt
from app.payments.razorpay_client import create_razorpay_order, verify_payment_signature
from app.policies.engine import evaluate_transaction, PolicyDecision
from app.schemas.commerce import CreatePaymentRequest, VerifyPaymentRequest, OrderOut

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create")
@limiter.limit("10/minute")
def create_payment(request: Request, payload: CreatePaymentRequest, db: Session = Depends(get_db)):
    intent = db.query(CheckoutIntent).filter(CheckoutIntent.id == payload.checkout_intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Checkout intent not found")
    if intent.policy_decision != PolicyDecision.ALLOWED.value or intent.buyer_approved is not True:
        raise HTTPException(status_code=400, detail="This checkout intent is not cleared for payment")

    merchant = db.query(Merchant).filter(Merchant.id == intent.merchant_id).first()

    # Find or create the pending Order for this intent (idempotent on intent id).
    order = db.query(Order).filter(Order.checkout_intent_id == intent.id).first()
    if order is None:
        order = Order(
            merchant_id=merchant.id,
            checkout_intent_id=intent.id,
            line_items=intent.line_items,
            amount=intent.total,
            currency=intent.currency,
            payment_status="pending",
            order_status="pending",
            is_ai_generated=True,
        )
        db.add(order)
        db.flush()
        log_event(
            db, merchant_id=merchant.id, session_id=intent.session_id, event_type="ORDER_CREATED",
            actor="system", amount=intent.total, result="success",
            output_data={"order_id": order.id},
        )

    prior_attempts = (
        db.query(PaymentAttempt)
        .filter(PaymentAttempt.checkout_intent_id == intent.id)
        .order_by(PaymentAttempt.attempt_number.desc())
        .all()
    )
    retry_count = len(prior_attempts)

    # Retry guardrail — re-run through the same policy engine used for money decisions.
    retry_check = evaluate_transaction(
        policy=merchant.policy, total_amount=intent.total, retry_count=retry_count,
        already_buyer_approved=True,
    )
    if retry_check.decision == PolicyDecision.BLOCKED and retry_count > 0:
        log_event(
            db, merchant_id=merchant.id, session_id=intent.session_id, event_type="RETRY_BLOCKED",
            actor="system", reason=retry_check.reason, amount=intent.total, result="failure",
        )
        db.commit()
        raise HTTPException(status_code=409, detail=retry_check.reason)

    idempotency_key = f"{intent.id}:{retry_count + 1}"
    existing_same_attempt = (
        db.query(PaymentAttempt).filter(PaymentAttempt.idempotency_key == idempotency_key).first()
    )
    if existing_same_attempt:
        # Exact same attempt already exists — return it rather than creating a duplicate.
        return {
            "order_id": order.id,
            "payment_attempt_id": existing_same_attempt.id,
            "razorpay_order_id": existing_same_attempt.razorpay_order_id,
            "amount": existing_same_attempt.amount,
            "currency": existing_same_attempt.currency,
        }

    rp_order = create_razorpay_order(amount_rupees=intent.total, currency=intent.currency, receipt=idempotency_key)
    if rp_order.get("error"):
        attempt = PaymentAttempt(
            order_id=order.id, checkout_intent_id=intent.id, idempotency_key=idempotency_key,
            attempt_number=retry_count + 1, amount=intent.total, currency=intent.currency,
            status="failed", failure_reason=rp_order.get("detail"),
        )
        db.add(attempt)
        db.commit()
        log_event(
            db, merchant_id=merchant.id, session_id=intent.session_id, event_type="PAYMENT_FAILED",
            actor="system", reason=rp_order.get("detail"), amount=intent.total, result="failure",
        )
        raise HTTPException(status_code=502, detail=rp_order.get("detail", "Razorpay order creation failed"))

    attempt = PaymentAttempt(
        order_id=order.id, checkout_intent_id=intent.id, idempotency_key=idempotency_key,
        attempt_number=retry_count + 1, amount=intent.total, currency=intent.currency,
        razorpay_order_id=rp_order["id"], status="created",
    )
    db.add(attempt)
    order.razorpay_order_id = rp_order["id"]
    db.commit()
    db.refresh(attempt)

    log_event(
        db, merchant_id=merchant.id, session_id=intent.session_id, event_type="PAYMENT_CREATED",
        actor="system", amount=intent.total, result="pending",
        output_data={"razorpay_order_id": rp_order["id"], "attempt_number": attempt.attempt_number},
    )

    return {
        "order_id": order.id,
        "payment_attempt_id": attempt.id,
        "razorpay_order_id": rp_order["id"],
        "razorpay_key_id": get_settings().razorpay_key_id,
        "amount": intent.total,
        "currency": intent.currency,
    }


@router.post("/verify", response_model=OrderOut)
def verify_payment(payload: VerifyPaymentRequest, db: Session = Depends(get_db)):
    attempt = (
        db.query(PaymentAttempt)
        .filter(PaymentAttempt.razorpay_order_id == payload.razorpay_order_id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Payment attempt not found for this Razorpay order")

    order = db.query(Order).filter(Order.id == attempt.order_id).first()
    intent = db.query(CheckoutIntent).filter(CheckoutIntent.id == attempt.checkout_intent_id).first()

    valid = verify_payment_signature(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )

    if not valid:
        attempt.status = "failed"
        attempt.failure_reason = "Signature verification failed"
        order.payment_status = "failed"
        db.commit()
        log_event(
            db, merchant_id=order.merchant_id, session_id=intent.session_id if intent else None,
            event_type="PAYMENT_FAILED", actor="system", reason="Signature verification failed",
            amount=order.amount, result="failure",
        )
        raise HTTPException(status_code=400, detail="Payment verification failed")

    attempt.status = "successful"
    attempt.razorpay_payment_id = payload.razorpay_payment_id
    attempt.razorpay_signature = payload.razorpay_signature

    order.payment_status = "paid"
    order.order_status = "completed"
    order.razorpay_payment_id = payload.razorpay_payment_id
    db.commit()
    db.refresh(order)

    log_event(
        db, merchant_id=order.merchant_id, session_id=intent.session_id if intent else None,
        event_type="PAYMENT_SUCCESS", actor="system", amount=order.amount, result="success",
        output_data={"razorpay_payment_id": payload.razorpay_payment_id},
    )
    return order


@router.get("/status/{payment_attempt_id}")
def payment_status(payment_attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.query(PaymentAttempt).filter(PaymentAttempt.id == payment_attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Payment attempt not found")
    return {
        "id": attempt.id,
        "status": attempt.status,
        "attempt_number": attempt.attempt_number,
        "failure_reason": attempt.failure_reason,
    }
