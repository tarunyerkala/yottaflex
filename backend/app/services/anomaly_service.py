import datetime
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.models import (
    AnomalyRecord, Interview, InterviewPanelMember, InterviewerAvailability,
    Application, Offer, JobRequisition, Feedback
)
from backend.app.audit.audit_service import log_audit_event


def scan_and_record_anomalies(db: Session, actor: str = "Anomaly Detector Engine") -> List[AnomalyRecord]:
    detected = []

    # Category A: Interviewer availability conflict / Double-booking
    interviews = db.query(Interview).filter(Interview.status.in_(["Scheduled", "Rescheduled"])).all()
    for intv in interviews:
        for pm in intv.panel_members:
            inv = pm.interviewer
            # Check double-booking
            double_booked = db.query(Interview).join(InterviewPanelMember).filter(
                InterviewPanelMember.interviewer_id == inv.id,
                Interview.id != intv.id,
                Interview.status.in_(["Scheduled", "Rescheduled"]),
                Interview.scheduled_start < intv.scheduled_end,
                Interview.scheduled_end > intv.scheduled_start
            ).first()

            if double_booked:
                rec = _get_or_create_anomaly(
                    db=db,
                    anomaly_id=f"ANOM-A-{intv.id}-{inv.id}",
                    issue_type="AVAILABILITY_CONFLICT",
                    entity_type="Interview",
                    entity_id=intv.interview_id,
                    severity="High",
                    description=f"Interviewer {inv.full_name} is double-booked between {intv.interview_id} and {double_booked.interview_id}.",
                    expected_state="Interviewer has mutually exclusive non-overlapping interview slots",
                    actual_state=f"Overlapping schedule ({intv.scheduled_start} to {intv.scheduled_end}) and ({double_booked.scheduled_start} to {double_booked.scheduled_end})",
                    violated_rule="INTERVIEWER_DOUBLE_BOOKED"
                )
                detected.append(rec)

    # Category B: Duplicate Candidate Application
    # Applications where is_duplicate is True, or same candidate and req have multiple records
    duplicate_apps = db.query(Application).filter(Application.is_duplicate == True).all()
    for dapp in duplicate_apps:
        rec = _get_or_create_anomaly(
            db=db,
            anomaly_id=f"ANOM-B-{dapp.id}",
            issue_type="DUPLICATE_APPLICATION",
            entity_type="Application",
            entity_id=dapp.application_id,
            severity="Medium",
            description=f"Duplicate submission detected for candidate {dapp.candidate.candidate_id} on requisition {dapp.requisition.requisition_id}.",
            expected_state="Candidate should have exactly one active application per requisition",
            actual_state=f"Multiple submissions recorded with preserved evidence",
            violated_rule="DUPLICATE_APPLICATION_POLICY"
        )
        detected.append(rec)

    # Category C: Missing feedback but advanced stage
    advanced_apps = db.query(Application).filter(
        Application.stage.in_(["Final Review", "Offer Pending Approval", "Offer Extended", "Hired"])
    ).all()
    for aapp in advanced_apps:
        for intv in aapp.interviews:
            panel_count = len(intv.panel_members)
            feedback_count = len(intv.feedbacks)
            if feedback_count < panel_count:
                rec = _get_or_create_anomaly(
                    db=db,
                    anomaly_id=f"ANOM-C-{aapp.id}-{intv.id}",
                    issue_type="MISSING_FEEDBACK_ADVANCED_STAGE",
                    entity_type="Application",
                    entity_id=aapp.application_id,
                    severity="High",
                    description=f"Application {aapp.application_id} advanced to stage '{aapp.stage}' while interview {intv.interview_id} only had {feedback_count}/{panel_count} feedbacks submitted.",
                    expected_state="Stage progression beyond Interview Evaluation requires all panel member feedbacks",
                    actual_state=f"Application is in '{aapp.stage}' with incomplete feedback",
                    violated_rule="STAGE_PROGRESSION_FEEDBACK_GATE"
                )
                detected.append(rec)

    # Category D: Offer outside approved salary band
    offers = db.query(Offer).all()
    for off in offers:
        req = off.application.requisition
        if off.proposed_salary < req.min_salary or off.proposed_salary > req.max_salary:
            rec = _get_or_create_anomaly(
                db=db,
                anomaly_id=f"ANOM-D-{off.id}",
                issue_type="SALARY_BAND_VIOLATION",
                entity_type="Offer",
                entity_id=off.offer_id,
                severity="Critical",
                description=f"Offer {off.offer_id} has proposed salary ${off.proposed_salary:,.2f}, which is outside approved band [${req.min_salary:,.2f} - ${req.max_salary:,.2f}].",
                expected_state=f"Proposed salary within [${req.min_salary:,.2f} - ${req.max_salary:,.2f}]",
                actual_state=f"Proposed salary is ${off.proposed_salary:,.2f}",
                violated_rule="SALARY_BAND_APPROVAL_LIMIT"
            )
            detected.append(rec)

    # Category E: Closed requisition with active applications
    closed_reqs = db.query(JobRequisition).filter(JobRequisition.status == "Closed").all()
    for creq in closed_reqs:
        active_apps = [
            app for app in creq.applications
            if app.stage not in ["Hired", "Rejected", "Withdrawn"]
        ]
        if active_apps:
            app_ids = [a.application_id for a in active_apps]
            rec = _get_or_create_anomaly(
                db=db,
                anomaly_id=f"ANOM-E-{creq.id}",
                issue_type="CLOSED_REQUISITION_ACTIVE_APPLICATIONS",
                entity_type="JobRequisition",
                entity_id=creq.requisition_id,
                severity="High",
                description=f"Requisition {creq.requisition_id} is Closed but has {len(active_apps)} active applications ({', '.join(app_ids[:3])}{'...' if len(app_ids) > 3 else ''}).",
                expected_state="All applications resolved or explicitly disposed prior to closing requisition",
                actual_state=f"Requisition is Closed with active applications",
                violated_rule="REQUISITION_DISPOSITION_POLICY"
            )
            detected.append(rec)

    db.commit()
    return detected


def _get_or_create_anomaly(
    db: Session,
    anomaly_id: str,
    issue_type: str,
    entity_type: str,
    entity_id: str,
    severity: str,
    description: str,
    expected_state: str,
    actual_state: str,
    violated_rule: str
) -> AnomalyRecord:
    existing = db.query(AnomalyRecord).filter(AnomalyRecord.anomaly_id == anomaly_id).first()
    if existing:
        return existing

    record = AnomalyRecord(
        anomaly_id=anomaly_id,
        issue_type=issue_type,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
        description=description,
        expected_state=expected_state,
        actual_state=actual_state,
        violated_rule=violated_rule,
        detected_at=datetime.datetime.utcnow(),
        is_resolved=False
    )
    db.add(record)
    db.flush()

    log_audit_event(
        db=db,
        event_type="ANOMALY_DETECTED",
        entity_type=entity_type,
        entity_id=entity_id,
        actor="Anomaly Detector",
        new_state=issue_type,
        reason=description
    )

    return record
