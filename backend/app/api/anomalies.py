from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import AnomalyRecord
from backend.app.schemas.schemas import AnomalyRecordRead, AnomalyResolveRequest
from backend.app.services.anomaly_service import scan_and_record_anomalies

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])

@router.get("", response_model=List[AnomalyRecordRead])
def list_anomalies(
    issue_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(AnomalyRecord)
    if issue_type:
        query = query.filter(AnomalyRecord.issue_type == issue_type)
    if severity:
        query = query.filter(AnomalyRecord.severity == severity)
    if is_resolved is not None:
        query = query.filter(AnomalyRecord.is_resolved == is_resolved)
    return query.order_by(AnomalyRecord.id.desc()).offset(offset).limit(limit).all()

@router.post("/scan", response_model=List[AnomalyRecordRead])
def run_scan(db: Session = Depends(get_db)):
    return scan_and_record_anomalies(db)

@router.post("/{id}/resolve", response_model=AnomalyRecordRead)
def resolve_anomaly(id: int, req: AnomalyResolveRequest, db: Session = Depends(get_db)):
    rec = db.query(AnomalyRecord).filter(AnomalyRecord.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Anomaly record not found.")
    rec.is_resolved = True
    rec.resolution_notes = req.resolution_notes
    db.commit()
    db.refresh(rec)
    return rec
