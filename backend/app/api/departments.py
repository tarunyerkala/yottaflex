import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import Department
from backend.app.schemas.schemas import DepartmentRead, DepartmentCreate

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentRead])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).order_by(Department.id).all()

@router.post("", response_model=DepartmentRead, status_code=201)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Department).filter(
        (Department.department_id == dept_in.department_id) | (Department.name == dept_in.name)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Department with this ID or Name already exists.")

    dept = Department(
        department_id=dept_in.department_id,
        name=dept_in.name,
        code=dept_in.code,
        cost_center=dept_in.cost_center,
        created_at=datetime.datetime.utcnow()
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
