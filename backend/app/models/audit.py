from sqlalchemy import Column, Float, String, ForeignKey, JSON
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class AuditEvent(Base, UUIDMixin, TimestampMixin):
    """
    Append-only. Every AI action and every financial action writes here.
    Nothing about this table is ever mutated or deleted by application code.
    """
    __tablename__ = "audit_events"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("agent_sessions.id"), nullable=True, index=True)

    event_type = Column(String, nullable=False, index=True)
    # e.g. AI_SESSION_STARTED, PRODUCT_SEARCH, PRODUCT_RECOMMENDED, UPSELL_SUGGESTED,
    # BUYER_APPROVAL_REQUESTED, BUYER_APPROVED, POLICY_CHECK, PAYMENT_CREATED,
    # PAYMENT_SUCCESS, PAYMENT_FAILED, RETRY_BLOCKED, ORDER_CREATED

    actor = Column(String, default="agent")  # agent | buyer | merchant | system

    reason = Column(String, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)

    policy_decision = Column(String, nullable=True)  # ALLOWED | REQUIRES_APPROVAL | BLOCKED | null
    amount = Column(Float, nullable=True)
    result = Column(String, nullable=True)  # success | failure | pending
