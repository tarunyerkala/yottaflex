import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import Interview, Feedback, Interviewer
from backend.app.schemas.schemas import FeedbackCreate
from backend.app.rules.business_rules import validate_feedback_submission, BusinessRuleViolation
from backend.app.audit.audit_service import log_audit_event


def submit_interview_feedback(
    db: Session,
    interview_id: int,
    fb_in: FeedbackCreate
) -> Feedback:
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    interviewer = db.query(Interviewer).filter(Interviewer.id == fb_in.interviewer_id).first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found.")

    scores = {
        "technical": fb_in.technical_score,
        "problem_solving": fb_in.problem_solving_score,
        "communication": fb_in.communication_score,
        "role_competency": fb_in.role_competency_score
    }

    try:
        validate_feedback_submission(
            db=db,
            interview=interview,
            interviewer_id=fb_in.interviewer_id,
            scores=scores,
            recommendation=fb_in.overall_recommendation
        )
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=e.code, detail=e.message)

    # Check for existing feedback
    existing = db.query(Feedback).filter(
        Feedback.interview_id == interview.id,
        Feedback.interviewer_id == fb_in.interviewer_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Interviewer {interviewer.full_name} has already submitted feedback for interview {interview.interview_id}."
        )

    # Business ID: FB-<interview-id>-<interviewer-id>
    feedback_id = f"FB-{interview.interview_id}-{interviewer.interviewer_id}"

    feedback = Feedback(
        feedback_id=feedback_id,
        interview_id=interview.id,
        interviewer_id=fb_in.interviewer_id,
        technical_score=fb_in.technical_score,
        problem_solving_score=fb_in.problem_solving_score,
        communication_score=fb_in.communication_score,
        role_competency_score=fb_in.role_competency_score,
        overall_recommendation=fb_in.overall_recommendation,
        strengths=fb_in.strengths,
        concerns=fb_in.concerns,
        comments=fb_in.comments,
        submitted_at=datetime.datetime.utcnow(),
        status="Submitted"
    )
    db.add(feedback)
    db.flush()

    # If all assigned panel members have submitted feedback, mark interview completed
    panel_count = len(interview.panel_members)
    current_fb_count = db.query(Feedback).filter(Feedback.interview_id == interview.id).count()
    if current_fb_count >= panel_count and interview.status != "Cancelled":
        interview.status = "Completed"

    log_audit_event(
        db=db,
        event_type="FEEDBACK_SUBMITTED",
        entity_type="Feedback",
        entity_id=feedback.feedback_id,
        actor=interviewer.full_name,
        new_state=fb_in.overall_recommendation,
        reason=f"Recommendation: {fb_in.overall_recommendation}"
    )

    db.commit()
    db.refresh(feedback)
    return feedback
