from sqlalchemy import Column, Float, String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class CheckoutIntent(Base, UUIDMixin, TimestampMixin):
    """
    Created by the AI's create_checkout_intent tool. Immutable snapshot of what's being bought.
    This is what the Policy Engine evaluates — never the raw LLM output.
    """
    __tablename__ = "checkout_intents"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("agent_sessions.id"), nullable=True)

    line_items = Column(JSON, nullable=False)  # [{product_id, name, price, qty}]
    subtotal = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    currency = Column(String, default="INR")

    idempotency_key = Column(String, unique=True, nullable=False, index=True)

    policy_decision = Column(String, nullable=True)  # ALLOWED | REQUIRES_APPROVAL | BLOCKED
    policy_reason = Column(String, nullable=True)

    requires_approval = Column(Boolean, default=False)
    buyer_approved = Column(Boolean, nullable=True)  # null = pending

    status = Column(String, default="created")  # created, approved, cancelled, converted


class Order(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "orders"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    checkout_intent_id = Column(String, ForeignKey("checkout_intents.id"), nullable=True)

    customer_ref = Column(String, nullable=True)
    line_items = Column(JSON, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")

    payment_status = Column(String, default="pending")  # pending, paid, failed
    order_status = Column(String, default="pending")    # pending, processing, completed, cancelled
    is_ai_generated = Column(Boolean, default=True)

    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
