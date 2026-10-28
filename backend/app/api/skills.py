from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.models import Skill
from backend.app.schemas.schemas import SkillRead

router = APIRouter(prefix="/skills", tags=["Skills"])

@router.get("", response_model=List[SkillRead])
def list_skills(db: Session = Depends(get_db)):
    return db.query(Skill).order_by(Skill.name).all()
