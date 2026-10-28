from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import AuditEvent
from backend.app.schemas.schemas import AuditEventRead

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("", response_model=List[AuditEventRead])
def get_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    return query.order_by(AuditEvent.id.desc()).offset(offset).limit(limit).all()
