from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from backend.app.db.database import get_db
from backend.app.models.models import JobRequisition, RequisitionSkill
from backend.app.schemas.schemas import (
    JobRequisitionRead, JobRequisitionCreate, JobRequisitionApprovalRequest
)
from backend.app.services.requisition_service import (
    create_requisition, approve_requisition, close_requisition
)

router = APIRouter(prefix="/requisitions", tags=["Requisitions"])

def _format_req(req: JobRequisition) -> dict:
    dept_name = req.department.name if req.department else None
    skills = [rs.skill.name for rs in req.requisition_skills if rs.skill]
    return {
        "id": req.id,
        "requisition_id": req.requisition_id,
        "title": req.title,
        "department_id": req.department_id,
        "location": req.location,
        "job_description": req.job_description,
        "employment_type": req.employment_type,
        "openings": req.openings,
        "min_salary": req.min_salary,
        "max_salary": req.max_salary,
        "currency": req.currency,
        "min_experience_months": req.min_experience_months,
        "requisition_owner": req.requisition_owner,
        "approver": req.approver,
        "approval_status": req.approval_status,
        "status": req.status,
        "opening_date": req.opening_date,
        "closing_date": req.closing_date,
        "created_at": req.created_at,
        "updated_at": req.updated_at,
        "department_name": dept_name,
        "required_skills": skills
    }

@router.get("", response_model=List[JobRequisitionRead])
def list_requisitions(
    status: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(JobRequisition).options(
        selectinload(JobRequisition.department),
        selectinload(JobRequisition.requisition_skills).selectinload(RequisitionSkill.skill)
    )
    if status:
        query = query.filter(JobRequisition.status == status)
    if department_id:
        query = query.filter(JobRequisition.department_id == department_id)
    reqs = query.order_by(JobRequisition.id.desc()).offset(offset).limit(limit).all()
    return [_format_req(r) for r in reqs]

@router.get("/{id}", response_model=JobRequisitionRead)
def get_requisition(id: int, db: Session = Depends(get_db)):
    req = db.query(JobRequisition).filter(JobRequisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found.")
    return _format_req(req)

@router.post("", response_model=JobRequisitionRead, status_code=201)
def create_new_requisition(req_in: JobRequisitionCreate, db: Session = Depends(get_db)):
    req = create_requisition(db, req_in)
    return _format_req(req)

@router.post("/{id}/approve", response_model=JobRequisitionRead)
def approve_req(id: int, approval_in: JobRequisitionApprovalRequest, db: Session = Depends(get_db)):
    req = approve_requisition(db, id, approval_in)
    return _format_req(req)

@router.post("/{id}/close", response_model=JobRequisitionRead)
def close_req(id: int, db: Session = Depends(get_db)):
    req = close_requisition(db, id)
    return _format_req(req)
