from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import Interview, Interviewer, InterviewPanelMember, Application
from sqlalchemy.orm import selectinload
from backend.app.schemas.schemas import (
    InterviewRead, InterviewCreate, InterviewRescheduleRequest, InterviewerRead
)
from backend.app.services.interview_service import (
    schedule_interview, reschedule_interview, cancel_interview
)

router = APIRouter(prefix="/interviews", tags=["Interviews"])

def _format_interview(i: Interview) -> dict:
    cand_name = i.application.candidate.full_name if i.application and i.application.candidate else None
    req_title = i.application.requisition.title if i.application and i.application.requisition else None
    panel = [f"{pm.interviewer.full_name} ({pm.role})" for pm in i.panel_members if pm.interviewer]
    panel_details = [
        {
            "id": pm.id,
            "interviewer_id": pm.interviewer_id,
            "role": pm.role,
            "full_name": pm.interviewer.full_name if pm.interviewer else None,
            "interviewer_code": pm.interviewer.interviewer_id if pm.interviewer else None,
            "department": pm.interviewer.department.name if pm.interviewer and pm.interviewer.department else None
        }
        for pm in i.panel_members if pm.interviewer
    ]
    return {
        "id": i.id,
        "interview_id": i.interview_id,
        "application_id": i.application_id,
        "round_number": i.round_number,
        "interview_type": i.interview_type,
        "scheduled_start": i.scheduled_start,
        "scheduled_end": i.scheduled_end,
        "time_zone": i.time_zone,
        "meeting_mode": i.meeting_mode,
        "status": i.status,
        "created_at": i.created_at,
        "candidate_name": cand_name,
        "requisition_title": req_title,
        "panel_members": panel,
        "panel_details": panel_details
    }

@router.get("", response_model=List[InterviewRead])
def list_interviews(
    status: Optional[str] = Query(None),
    application_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Interview).options(
        selectinload(Interview.application).selectinload(Application.candidate),
        selectinload(Interview.application).selectinload(Application.requisition),
        selectinload(Interview.panel_members).selectinload(InterviewPanelMember.interviewer).selectinload(Interviewer.department)
    )
    if status:
        query = query.filter(Interview.status == status)
    if application_id:
        query = query.filter(Interview.application_id == application_id)
    interviews = query.order_by(Interview.id.desc()).offset(offset).limit(limit).all()
    return [_format_interview(i) for i in interviews]

@router.get("/{id}/panel")
def get_interview_panel(id: int, db: Session = Depends(get_db)):
    intv = db.query(Interview).filter(Interview.id == id).first()
    if not intv:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return [
        {
            "id": pm.id,
            "interviewer_id": pm.interviewer_id,
            "role": pm.role,
            "full_name": pm.interviewer.full_name if pm.interviewer else None,
            "interviewer_code": pm.interviewer.interviewer_id if pm.interviewer else None,
            "department": pm.interviewer.department.name if pm.interviewer and pm.interviewer.department else None
        }
        for pm in intv.panel_members if pm.interviewer
    ]

@router.get("/{id}", response_model=InterviewRead)
def get_interview(id: int, db: Session = Depends(get_db)):
    intv = db.query(Interview).filter(Interview.id == id).first()
    if not intv:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return _format_interview(intv)

@router.post("", response_model=InterviewRead, status_code=201)
def create_interview(int_in: InterviewCreate, db: Session = Depends(get_db)):
    intv = schedule_interview(db, int_in)
    return _format_interview(intv)

@router.post("/{id}/reschedule", response_model=InterviewRead)
def reschedule(id: int, req: InterviewRescheduleRequest, db: Session = Depends(get_db)):
    intv = reschedule_interview(db, id, req)
    return _format_interview(intv)

@router.post("/{id}/cancel", response_model=InterviewRead)
def cancel(id: int, db: Session = Depends(get_db)):
    intv = cancel_interview(db, id)
    return _format_interview(intv)
