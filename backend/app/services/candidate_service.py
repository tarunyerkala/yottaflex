import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import Candidate, CandidateSkill, ResumeArtifact
from backend.app.schemas.schemas import CandidateCreate
from backend.app.audit.audit_service import log_audit_event


def create_candidate(db: Session, cand_in: CandidateCreate, actor: str = "Recruiter") -> Candidate:
    # Check email uniqueness
    existing_email = db.query(Candidate).filter(Candidate.email == cand_in.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail=f"Candidate with email {cand_in.email} already exists.")

    existing_id = db.query(Candidate).filter(Candidate.candidate_id == cand_in.candidate_id).first()
    if existing_id:
        raise HTTPException(status_code=409, detail=f"Candidate ID {cand_in.candidate_id} already exists.")

    candidate = Candidate(
        candidate_id=cand_in.candidate_id,
        full_name=cand_in.full_name,
        email=cand_in.email,
        phone=cand_in.phone,
        total_experience_months=cand_in.total_experience_months,
        current_location=cand_in.current_location,
        profile_summary=cand_in.profile_summary
    )
    db.add(candidate)
    db.flush()

    if cand_in.skills:
        for sk in cand_in.skills:
            cand_skill = CandidateSkill(
                candidate_id=candidate.id,
                skill_id=sk.skill_id,
                proficiency_level=sk.proficiency_level,
                experience_months=sk.experience_months,
                evidence_source=sk.evidence_source,
                last_verified_date=datetime.date.today()
            )
            db.add(cand_skill)

    # Automatically create a synthetic resume artifact
    resume_artifact = ResumeArtifact(
        artifact_id=f"RES-{candidate.candidate_id.replace('CAND-', '')}",
        candidate_id=candidate.id,
        file_name=f"{candidate.full_name.lower().replace(' ', '_')}_resume.pdf",
        mime_type="application/pdf",
        file_size_bytes=14200,
        storage_reference=f"synthetic_storage/resumes/{candidate.candidate_id}.pdf",
        processing_status="Processed",
        source_method="SyntheticGenerator"
    )
    db.add(resume_artifact)

    log_audit_event(
        db=db,
        event_type="CANDIDATE_CREATED",
        entity_type="Candidate",
        entity_id=candidate.candidate_id,
        actor=actor,
        new_state="Created",
        reason="Candidate profile created"
    )

    db.commit()
    db.refresh(candidate)
    return candidate
