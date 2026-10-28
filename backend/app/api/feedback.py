from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import Feedback, Interview
from backend.app.schemas.schemas import FeedbackRead, FeedbackCreate
from backend.app.services.feedback_service import submit_interview_feedback

router = APIRouter(prefix="/interviews", tags=["Feedback"])

def _format_feedback(fb: Feedback) -> dict:
    return {
        "id": fb.id,
        "feedback_id": fb.feedback_id,
        "interview_id": fb.interview_id,
        "interviewer_id": fb.interviewer_id,
        "interviewer_name": fb.interviewer.full_name if fb.interviewer else None,
        "technical_score": fb.technical_score,
        "problem_solving_score": fb.problem_solving_score,
        "communication_score": fb.communication_score,
        "role_competency_score": fb.role_competency_score,
        "overall_recommendation": fb.overall_recommendation,
        "strengths": fb.strengths,
        "concerns": fb.concerns,
        "comments": fb.comments,
        "submitted_at": fb.submitted_at,
        "status": fb.status
    }

@router.get("/{id}/feedback", response_model=List[FeedbackRead])
def get_interview_feedback(id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    feedbacks = db.query(Feedback).filter(Feedback.interview_id == id).all()
    return [_format_feedback(fb) for fb in feedbacks]

@router.post("/{id}/feedback", response_model=FeedbackRead, status_code=201)
def submit_feedback(id: int, fb_in: FeedbackCreate, db: Session = Depends(get_db)):
    fb = submit_interview_feedback(db, id, fb_in)
    return _format_feedback(fb)
