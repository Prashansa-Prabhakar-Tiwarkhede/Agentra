"""
Razorpay integration — TEST MODE only.

This module is deliberately the ONLY place that imports the razorpay SDK.
It is never imported by app/agents/*, so the LLM layer has no code path
that can reach a payment call.
"""
import razorpay

from app.config import get_settings

settings = get_settings()


def _client() -> razorpay.Client | None:
    if not settings.is_razorpay_configured:
        return None
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    return client


def create_razorpay_order(*, amount_rupees: float, currency: str, receipt: str) -> dict:
    """amount_rupees is converted to paise as Razorpay requires integer paise."""
    client = _client()
    if client is None:
        return {"error": "RAZORPAY_NOT_CONFIGURED", "detail": "Add RAZORPAY_KEY_ID/SECRET to .env"}
    try:
        order = client.order.create({
            "amount": int(round(amount_rupees * 100)),
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1,
        })
        return order
    except Exception as e:
        return {"error": "RAZORPAY_ORDER_FAILED", "detail": str(e)}


def verify_payment_signature(*, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    client = _client()
    if client is None:
        return False
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def fetch_payment_status(payment_id: str) -> dict:
    client = _client()
    if client is None:
        return {"error": "RAZORPAY_NOT_CONFIGURED"}
    try:
        return client.payment.fetch(payment_id)
    except Exception as e:
        return {"error": "RAZORPAY_FETCH_FAILED", "detail": str(e)}
