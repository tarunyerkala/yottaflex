import datetime
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import (
    Application, Candidate, JobRequisition, ApplicationStageHistory
)
from backend.app.schemas.schemas import ApplicationCreate, ApplicationTransitionRequest
from backend.app.rules.business_rules import (
    validate_requisition_can_accept_application,
    validate_stage_transition,
    BusinessRuleViolation
)
from backend.app.audit.audit_service import log_audit_event


def submit_application(db: Session, app_in: ApplicationCreate, actor: str = "Candidate Portal") -> Application:
    candidate = db.query(Candidate).filter(Candidate.id == app_in.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    requisition = db.query(JobRequisition).filter(JobRequisition.id == app_in.requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found.")

    # Business rule: Requisition must be approved and open
    try:
        validate_requisition_can_accept_application(requisition)
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=e.code, detail=e.message)

    # Business rule: Duplicate check
    existing_app = db.query(Application).filter(
        Application.candidate_id == app_in.candidate_id,
        Application.requisition_id == app_in.requisition_id,
        Application.stage != "Withdrawn"
    ).first()

    if existing_app:
        raise HTTPException(
            status_code=409,
            detail=f"Candidate {candidate.candidate_id} already has an active application {existing_app.application_id} for requisition {requisition.requisition_id}."
        )

    # Prescribed deterministic naming convention: APP-<requisition-id>-<candidate-id>
    app_id = f"APP-{requisition.requisition_id}-{candidate.candidate_id}"

    application = Application(
        application_id=app_id,
        candidate_id=candidate.id,
        requisition_id=requisition.id,
        application_date=datetime.datetime.utcnow(),
        source=app_in.source,
        stage="Applied",
        status="Active",
        is_duplicate=False
    )
    db.add(application)
    db.flush()

    # Record initial stage history
    hist = ApplicationStageHistory(
        history_id=f"HIST-{uuid.uuid4().hex[:10].upper()}",
        application_id=application.id,
        from_stage="None",
        to_stage="Applied",
        actor=actor,
        reason="Application submitted",
        rule_version="v1.0"
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="APPLICATION_SUBMITTED",
        entity_type="Application",
        entity_id=application.application_id,
        actor=actor,
        new_state="Applied",
        reason="New application submitted"
    )

    db.commit()
    db.refresh(application)
    return application


def transition_application_stage(
    db: Session,
    app_id: int,
    req: ApplicationTransitionRequest
) -> Application:
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if application.stage == req.target_stage:
        raise HTTPException(
            status_code=400,
            detail=f"Application {application.application_id} is already at stage '{application.stage}'."
        )

    prev_stage = application.stage

    try:
        validate_stage_transition(db, application, req.target_stage)
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=e.code, detail=e.message)

    application.stage = req.target_stage
    if req.target_stage in ["Hired", "Rejected", "Withdrawn"]:
        application.status = "Closed"

    hist = ApplicationStageHistory(
        history_id=f"HIST-{uuid.uuid4().hex[:10].upper()}",
        application_id=application.id,
        from_stage=prev_stage,
        to_stage=req.target_stage,
        actor=req.actor,
        reason=req.reason or f"Transitioned from {prev_stage} to {req.target_stage}",
        rule_version="v1.0"
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="STAGE_PROGRESSION",
        entity_type="Application",
        entity_id=application.application_id,
        actor=req.actor,
        previous_state=prev_stage,
        new_state=req.target_stage,
        reason=req.reason
    )

    db.commit()
    db.refresh(application)
    return application
