from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from backend.app.db.database import get_db
from backend.app.models.models import Candidate, CandidateSkill
from backend.app.schemas.schemas import CandidateRead, CandidateCreate
from backend.app.services.candidate_service import create_candidate

router = APIRouter(prefix="/candidates", tags=["Candidates"])

def _format_candidate(c: Candidate) -> dict:
    skills = [
        {
            "id": cs.id,
            "skill_id": cs.skill_id,
            "skill_name": cs.skill.name if cs.skill else None,
            "proficiency_level": cs.proficiency_level,
            "experience_months": cs.experience_months,
            "evidence_source": cs.evidence_source
        }
        for cs in c.candidate_skills
    ]
    resumes = [
        {
            "id": r.id,
            "artifact_id": r.artifact_id,
            "file_name": r.file_name,
            "mime_type": r.mime_type,
            "file_size_bytes": r.file_size_bytes,
            "processing_status": r.processing_status,
            "source_method": r.source_method,
            "created_at": r.created_at
        }
        for r in c.resumes
    ]
    return {
        "id": c.id,
        "candidate_id": c.candidate_id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "total_experience_months": c.total_experience_months,
        "current_location": c.current_location,
        "profile_summary": c.profile_summary,
        "created_at": c.created_at,
        "skills": skills,
        "resumes": resumes
    }

@router.get("", response_model=List[CandidateRead])
def list_candidates(
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=3000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Candidate).options(
        selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill),
        selectinload(Candidate.resumes)
    )
    if search:
        query = query.filter(
            (Candidate.full_name.ilike(f"%{search}%")) |
            (Candidate.email.ilike(f"%{search}%")) |
            (Candidate.candidate_id.ilike(f"%{search}%"))
        )
    candidates = query.order_by(Candidate.id.desc()).offset(offset).limit(limit).all()
    return [_format_candidate(c) for c in candidates]

@router.get("/{id}", response_model=CandidateRead)
def get_candidate(id: int, db: Session = Depends(get_db)):
    cand = db.query(Candidate).filter(Candidate.id == id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return _format_candidate(cand)

@router.post("", response_model=CandidateRead, status_code=201)
def create_new_candidate(cand_in: CandidateCreate, db: Session = Depends(get_db)):
    cand = create_candidate(db, cand_in)
    return _format_candidate(cand)
