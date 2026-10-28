from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.schemas.schemas import OverviewMetrics, FunnelMetrics, ExceptionSummary
from backend.app.analytics.metrics_service import (
    get_overview_metrics, get_funnel_metrics, get_stage_distribution,
    get_department_distribution, get_exception_summary
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=OverviewMetrics)
def overview(db: Session = Depends(get_db)):
    return get_overview_metrics(db)

@router.get("/funnel", response_model=FunnelMetrics)
def funnel(db: Session = Depends(get_db)):
    return get_funnel_metrics(db)

@router.get("/stages")
def stages(db: Session = Depends(get_db)):
    return get_stage_distribution(db)

@router.get("/departments")
def departments(db: Session = Depends(get_db)):
    return get_department_distribution(db)

@router.get("/exceptions", response_model=ExceptionSummary)
def exceptions(db: Session = Depends(get_db)):
    return get_exception_summary(db)
