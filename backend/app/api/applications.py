from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from backend.app.db.database import get_db
from backend.app.models.models import Application, ApplicationStageHistory, ScreeningEvaluation
from backend.app.schemas.schemas import (
    ApplicationRead, ApplicationCreate, ApplicationTransitionRequest,
    ApplicationStageHistoryRead, ScreeningEvaluationRead
)
from backend.app.services.application_service import submit_application, transition_application_stage
from backend.app.services.screening_service import run_screening_for_application

router = APIRouter(prefix="/applications", tags=["Applications"])

def _format_application(a: Application) -> dict:
    return {
        "id": a.id,
        "application_id": a.application_id,
        "candidate_id": a.candidate_id,
        "requisition_id": a.requisition_id,
        "application_date": a.application_date,
        "source": a.source,
        "stage": a.stage,
        "status": a.status,
        "screening_score": a.screening_score,
        "screening_decision": a.screening_decision,
        "decision_reason": a.decision_reason,
        "is_duplicate": a.is_duplicate,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
        "candidate_name": a.candidate.full_name if a.candidate else None,
        "requisition_title": a.requisition.title if a.requisition else None
    }

@router.get("", response_model=List[ApplicationRead])
def list_applications(
    stage: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    requisition_id: Optional[int] = Query(None),
    candidate_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Application).options(
        selectinload(Application.candidate),
        selectinload(Application.requisition)
    )
    if stage:
        query = query.filter(Application.stage == stage)
    if status:
        query = query.filter(Application.status == status)
    if requisition_id:
        query = query.filter(Application.requisition_id == requisition_id)
    if candidate_id:
        query = query.filter(Application.candidate_id == candidate_id)

    apps = query.order_by(Application.id.desc()).offset(offset).limit(limit).all()
    return [_format_application(a) for a in apps]

@router.get("/{id}", response_model=ApplicationRead)
def get_application(id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return _format_application(app)

@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db)):
    app = submit_application(db, app_in)
    return _format_application(app)

@router.get("/{id}/history", response_model=List[ApplicationStageHistoryRead])
def get_application_history(id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return db.query(ApplicationStageHistory).filter(
        ApplicationStageHistory.application_id == id
    ).order_by(ApplicationStageHistory.id.asc()).all()

@router.post("/{id}/screen", response_model=ScreeningEvaluationRead)
def screen_application(id: int, db: Session = Depends(get_db)):
    return run_screening_for_application(db, id)

@router.post("/{id}/transition", response_model=ApplicationRead)
def transition_stage(
    id: int,
    req: ApplicationTransitionRequest,
    db: Session = Depends(get_db)
):
    app = transition_application_stage(db, id, req)
    return _format_application(app)

@router.get("/{id}/evaluation", response_model=Optional[ScreeningEvaluationRead])
def get_application_evaluation(id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    eval_record = db.query(ScreeningEvaluation).filter(ScreeningEvaluation.application_id == id).order_by(ScreeningEvaluation.id.desc()).first()
    return eval_record

