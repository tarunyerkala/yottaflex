from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.services.validator_service import run_all_validation_checks

router = APIRouter(prefix="/validation", tags=["Validation"])

@router.get("/summary")
def get_validation_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return run_all_validation_checks(db)

@router.post("/run")
def trigger_validation_run(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return run_all_validation_checks(db)
