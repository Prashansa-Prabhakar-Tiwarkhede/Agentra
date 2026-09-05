from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_merchant
from app.database import get_db
from app.models.audit import AuditEvent
from app.models.merchant import Merchant

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_events(
    session_id: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=100, le=500),
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    q = db.query(AuditEvent).filter(AuditEvent.merchant_id == merchant.id)
    if session_id:
        q = q.filter(AuditEvent.session_id == session_id)
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    events = q.order_by(AuditEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat(),
            "event_type": e.event_type,
            "actor": e.actor,
            "reason": e.reason,
            "input_data": e.input_data,
            "output_data": e.output_data,
            "policy_decision": e.policy_decision,
            "amount": e.amount,
            "result": e.result,
        }
        for e in events
    ]
