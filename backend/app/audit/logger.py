"""
Every AI action and every financial action must be logged here.
This module is the ONLY place that writes to the audit_events table,
so nothing important can get logged inconsistently or skipped.
"""
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def log_event(
    db: Session,
    *,
    merchant_id: str,
    event_type: str,
    session_id: str | None = None,
    actor: str = "agent",
    reason: str | None = None,
    input_data: dict | None = None,
    output_data: dict | None = None,
    policy_decision: str | None = None,
    amount: float | None = None,
    result: str | None = None,
    commit: bool = True,
) -> AuditEvent:
    event = AuditEvent(
        merchant_id=merchant_id,
        session_id=session_id,
        event_type=event_type,
        actor=actor,
        reason=reason,
        input_data=input_data,
        output_data=output_data,
        policy_decision=policy_decision,
        amount=amount,
        result=result,
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event
