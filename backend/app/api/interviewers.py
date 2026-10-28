from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import Interviewer
from backend.app.schemas.schemas import InterviewerRead, InterviewerCreate

router = APIRouter(prefix="/interviewers", tags=["Interviewers"])

def _format_interviewer(i: Interviewer) -> dict:
    return {
        "id": i.id,
        "interviewer_id": i.interviewer_id,
        "full_name": i.full_name,
        "email": i.email,
        "department_id": i.department_id,
        "department_name": i.department.name if i.department else None,
        "expertise_areas": i.expertise_areas,
        "is_active": i.is_active,
        "created_at": i.created_at
    }

@router.get("", response_model=List[InterviewerRead])
def list_interviewers(db: Session = Depends(get_db)):
    interviewers = db.query(Interviewer).order_by(Interviewer.id).all()
    return [_format_interviewer(i) for i in interviewers]
