import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import JobRequisition, RequisitionSkill, RequisitionApproval, Department
from backend.app.schemas.schemas import JobRequisitionCreate, JobRequisitionApprovalRequest
from backend.app.audit.audit_service import log_audit_event


def create_requisition(db: Session, req_in: JobRequisitionCreate, actor: str = "Recruiter") -> JobRequisition:
    # Check if department exists
    dept = db.query(Department).filter(Department.id == req_in.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department with ID {req_in.department_id} not found.")

    if req_in.min_salary > req_in.max_salary:
        raise HTTPException(status_code=400, detail="Minimum salary cannot exceed maximum salary.")

    # Check requisition_id uniqueness
    existing = db.query(JobRequisition).filter(JobRequisition.requisition_id == req_in.requisition_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Requisition ID {req_in.requisition_id} already exists.")

    requisition = JobRequisition(
        requisition_id=req_in.requisition_id,
        title=req_in.title,
        department_id=req_in.department_id,
        location=req_in.location,
        job_description=req_in.job_description,
        employment_type=req_in.employment_type,
        openings=req_in.openings,
        min_salary=req_in.min_salary,
        max_salary=req_in.max_salary,
        currency=req_in.currency,
        min_experience_months=req_in.min_experience_months,
        requisition_owner=req_in.requisition_owner,
        approval_status="Draft",
        status="Draft"
    )
    db.add(requisition)
    db.flush()

    if req_in.skills:
        for skill_item in req_in.skills:
            req_skill = RequisitionSkill(
                requisition_id=requisition.id,
                skill_id=skill_item.skill_id,
                is_mandatory=skill_item.is_mandatory,
                min_years_experience=skill_item.min_years_experience,
                importance_weight=skill_item.importance_weight
            )
            db.add(req_skill)

    log_audit_event(
        db=db,
        event_type="REQUISITION_CREATED",
        entity_type="JobRequisition",
        entity_id=requisition.requisition_id,
        actor=actor,
        new_state="Draft",
        reason="Initial requisition creation"
    )

    db.commit()
    db.refresh(requisition)
    return requisition


def approve_requisition(db: Session, req_id: int, approval_in: JobRequisitionApprovalRequest) -> JobRequisition:
    requisition = db.query(JobRequisition).filter(JobRequisition.id == req_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found.")

    if requisition.approval_status == "Approved" and approval_in.status == "Approved":
        raise HTTPException(status_code=400, detail=f"Requisition {requisition.requisition_id} is already approved.")

    prev_status = requisition.approval_status
    requisition.approval_status = approval_in.status
    requisition.approver = approval_in.approver

    if approval_in.status == "Approved":
        requisition.status = "Open"
        requisition.opening_date = datetime.date.today()
    elif approval_in.status == "Rejected":
        requisition.status = "Closed"

    approval_rec = RequisitionApproval(
        requisition_id=requisition.id,
        approver=approval_in.approver,
        status=approval_in.status,
        decision_date=datetime.datetime.utcnow(),
        comments=approval_in.comments
    )
    db.add(approval_rec)

    log_audit_event(
        db=db,
        event_type=f"REQUISITION_{approval_in.status.upper()}",
        entity_type="JobRequisition",
        entity_id=requisition.requisition_id,
        actor=approval_in.approver,
        previous_state=prev_status,
        new_state=approval_in.status,
        reason=approval_in.comments
    )

    db.commit()
    db.refresh(requisition)
    return requisition


def close_requisition(db: Session, req_id: int, actor: str = "Hiring Manager", reason: str = "Requisition closed") -> JobRequisition:
    requisition = db.query(JobRequisition).filter(JobRequisition.id == req_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found.")

    if requisition.status == "Closed":
        raise HTTPException(status_code=400, detail=f"Requisition {requisition.requisition_id} is already closed.")

    prev_status = requisition.status
    requisition.status = "Closed"
    requisition.closing_date = datetime.date.today()

    log_audit_event(
        db=db,
        event_type="REQUISITION_CLOSED",
        entity_type="JobRequisition",
        entity_id=requisition.requisition_id,
        actor=actor,
        previous_state=prev_status,
        new_state="Closed",
        reason=reason
    )

    db.commit()
    db.refresh(requisition)
    return requisition
