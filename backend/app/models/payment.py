from sqlalchemy import Column, Float, Integer, String, ForeignKey
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class PaymentAttempt(Base, UUIDMixin, TimestampMixin):
    """
    Every attempt to charge, including retries, is its own row.
    Idempotency key prevents duplicate Razorpay orders being created for the same intent.
    """
    __tablename__ = "payment_attempts"

    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    checkout_intent_id = Column(String, ForeignKey("checkout_intents.id"), nullable=False, index=True)

    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    attempt_number = Column(Integer, default=1)

    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")

    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)

    # created, processing, successful, failed, cancelled, retry_blocked
    status = Column(String, default="created")
    failure_reason = Column(String, nullable=True)
