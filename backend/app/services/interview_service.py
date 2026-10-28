import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import (
    Interview, InterviewPanelMember, Application, Interviewer
)
from backend.app.schemas.schemas import InterviewCreate, InterviewRescheduleRequest
from backend.app.rules.business_rules import validate_interview_scheduling, BusinessRuleViolation
from backend.app.audit.audit_service import log_audit_event


def schedule_interview(
    db: Session,
    int_in: InterviewCreate,
    actor: str = "Recruitment Coordinator"
) -> Interview:
    application = db.query(Application).filter(Application.id == int_in.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if application.stage not in ["Screening Passed", "Interview"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot schedule interview for application in stage '{application.stage}'. Must be in 'Screening Passed' or 'Interview'."
        )

    if not int_in.interviewer_ids:
        raise HTTPException(status_code=400, detail="At least one panel interviewer is required.")

    # Validate conflicts & availability
    try:
        validate_interview_scheduling(
            db=db,
            interviewer_ids=int_in.interviewer_ids,
            scheduled_start=int_in.scheduled_start,
            scheduled_end=int_in.scheduled_end
        )
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=e.code, detail=e.message)

    # Count existing interviews for ID formatting
    count = db.query(Interview).count() + 1
    interview_id = f"INT-2026-{count:06d}"

    interview = Interview(
        interview_id=interview_id,
        application_id=application.id,
        round_number=int_in.round_number,
        interview_type=int_in.interview_type,
        scheduled_start=int_in.scheduled_start,
        scheduled_end=int_in.scheduled_end,
        time_zone=int_in.time_zone,
        meeting_mode=int_in.meeting_mode,
        status="Scheduled"
    )
    db.add(interview)
    db.flush()

    for idx, inv_id in enumerate(int_in.interviewer_ids):
        role = "Lead Interviewer" if idx == 0 else "Panel Member"
        panel = InterviewPanelMember(
            interview_id=interview.id,
            interviewer_id=inv_id,
            role=role
        )
        db.add(panel)

    if application.stage == "Screening Passed":
        application.stage = "Interview"

    log_audit_event(
        db=db,
        event_type="INTERVIEW_SCHEDULED",
        entity_type="Interview",
        entity_id=interview.interview_id,
        actor=actor,
        new_state="Scheduled",
        reason=f"Scheduled {interview.interview_type} for application {application.application_id}"
    )

    db.commit()
    db.refresh(interview)
    return interview


def reschedule_interview(
    db: Session,
    interview_id: int,
    req: InterviewRescheduleRequest
) -> Interview:
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    panel_interviewer_ids = [p.interviewer_id for p in interview.panel_members]

    try:
        validate_interview_scheduling(
            db=db,
            interviewer_ids=panel_interviewer_ids,
            scheduled_start=req.scheduled_start,
            scheduled_end=req.scheduled_end,
            exclude_interview_id=interview.id
        )
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=e.code, detail=e.message)

    prev_time = f"{interview.scheduled_start} - {interview.scheduled_end}"
    interview.scheduled_start = req.scheduled_start
    interview.scheduled_end = req.scheduled_end
    interview.status = "Rescheduled"

    log_audit_event(
        db=db,
        event_type="INTERVIEW_RESCHEDULED",
        entity_type="Interview",
        entity_id=interview.interview_id,
        actor=req.actor,
        previous_state=prev_time,
        new_state=f"{req.scheduled_start} - {req.scheduled_end}",
        reason=req.reason
    )

    db.commit()
    db.refresh(interview)
    return interview


def cancel_interview(
    db: Session,
    interview_id: int,
    actor: str = "Coordinator",
    reason: str = "Candidate cancelled"
) -> Interview:
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    if interview.status == "Cancelled":
        raise HTTPException(status_code=400, detail=f"Interview {interview.interview_id} is already cancelled.")
    if interview.status == "Completed":
        raise HTTPException(status_code=400, detail=f"Cannot cancel a completed interview.")

    prev_status = interview.status
    interview.status = "Cancelled"

    log_audit_event(
        db=db,
        event_type="INTERVIEW_CANCELLED",
        entity_type="Interview",
        entity_id=interview.interview_id,
        actor=actor,
        previous_state=prev_status,
        new_state="Cancelled",
        reason=reason
    )

    db.commit()
    db.refresh(interview)
    return interview
