from pydantic import BaseModel
from typing import Literal


class ChatRequest(BaseModel):
    merchant_id: str
    session_id: str | None = None  # None -> start a new session
    message: str
    buyer_budget: float | None = None  # optional explicit override; usually parsed from message


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    structured_action: dict | None = None
    products: list[dict] = []
    cart_preview: dict | None = None


class LineItem(BaseModel):
    product_id: str
    name: str
    price: float
    qty: int = 1


class CreateCheckoutIntentRequest(BaseModel):
    merchant_id: str
    session_id: str | None = None
    line_items: list[LineItem]
    buyer_budget: float | None = None
    discount_percent: float = 0.0


class CheckoutIntentOut(BaseModel):
    id: str
    subtotal: float
    total: float
    currency: str
    policy_decision: str | None
    policy_reason: str | None
    requires_approval: bool
    buyer_approved: bool | None
    status: str

    class Config:
        from_attributes = True


class ApproveCheckoutRequest(BaseModel):
    checkout_intent_id: str
    approve: bool


class CreatePaymentRequest(BaseModel):
    checkout_intent_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderOut(BaseModel):
    id: str
    merchant_id: str
    line_items: list
    amount: float
    currency: str
    payment_status: str
    order_status: str
    is_ai_generated: bool
    razorpay_order_id: str | None
    razorpay_payment_id: str | None

    class Config:
        from_attributes = True


class AuditEventOut(BaseModel):
    id: str
    created_at: str
    event_type: str
    actor: str
    reason: str | None
    input_data: dict | None
    output_data: dict | None
    policy_decision: str | None
    amount: float | None
    result: str | None

    class Config:
        from_attributes = True
