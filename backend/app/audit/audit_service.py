import datetime
import uuid
from sqlalchemy.orm import Session
from backend.app.models.models import AuditEvent

def log_audit_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    previous_state: str = None,
    new_state: str = None,
    reason: str = None,
    correlation_id: str = None
) -> AuditEvent:
    event_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    event = AuditEvent(
        event_id=event_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor=actor,
        timestamp=datetime.datetime.utcnow(),
        previous_state=str(previous_state) if previous_state else None,
        new_state=str(new_state) if new_state else None,
        reason=reason,
        correlation_id=correlation_id
    )
    db.add(event)
    db.flush()
    return event
