import datetime
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import (
    Application, ScreeningRule, ScreeningEvaluation, ApplicationStageHistory
)
from backend.app.rules.business_rules import evaluate_candidate_screening
from backend.app.audit.audit_service import log_audit_event


def run_screening_for_application(
    db: Session,
    app_id: int,
    rule_id: Optional[str] = None,
    actor: str = "Automated Screening Engine"
) -> ScreeningEvaluation:
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if application.stage in ["Rejected", "Withdrawn", "Hired"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot screen application in terminal stage '{application.stage}'."
        )

    # Find applicable screening rule
    rule_query = db.query(ScreeningRule).filter(ScreeningRule.is_enabled == True)
    if rule_id:
        rule = rule_query.filter(ScreeningRule.rule_id == rule_id).first()
    else:
        rule = rule_query.first()

    if not rule:
        # Default fallback rule if none seeded
        rule = ScreeningRule(
            rule_id="RULE-001",
            name="Default Skill & Experience Rule",
            description="60% skill coverage + 40% experience normalization",
            applicable_job_family="All",
            criterion="SkillCoverageAndExperience",
            skill_weight=0.6,
            experience_weight=0.4,
            pass_threshold=70.0,
            rule_version="v1.0",
            is_enabled=True,
            effective_start_date=datetime.date(2026, 1, 1)
        )
        db.add(rule)
        db.flush()

    eval_result = evaluate_candidate_screening(
        db=db,
        candidate=application.candidate,
        requisition=application.requisition,
        rule=rule
    )

    evaluation = ScreeningEvaluation(
        evaluation_id=f"EVAL-{uuid.uuid4().hex[:10].upper()}",
        application_id=application.id,
        rule_version=eval_result["rule_version"],
        matched_skills_count=eval_result["matched_count"],
        total_required_skills=eval_result["total_required"],
        skill_coverage_pct=eval_result["skill_coverage_pct"],
        candidate_experience_months=eval_result["candidate_experience_months"],
        required_experience_months=eval_result["required_experience_months"],
        experience_score=eval_result["experience_score"],
        final_score=eval_result["final_score"],
        decision=eval_result["decision"],
        explanation=eval_result["explanation"],
        evaluated_at=datetime.datetime.utcnow()
    )
    db.add(evaluation)

    # Update application record
    application.screening_score = eval_result["final_score"]
    application.screening_decision = eval_result["decision"]
    application.decision_reason = eval_result["explanation"]

    prev_stage = application.stage
    new_stage = "Screening Passed" if eval_result["decision"] == "Pass" else "Screening Rejected"
    application.stage = new_stage

    hist = ApplicationStageHistory(
        history_id=f"HIST-{uuid.uuid4().hex[:10].upper()}",
        application_id=application.id,
        from_stage=prev_stage,
        to_stage=new_stage,
        actor=actor,
        reason=eval_result["explanation"],
        rule_version=eval_result["rule_version"]
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="SCREENING_EVALUATED",
        entity_type="Application",
        entity_id=application.application_id,
        actor=actor,
        previous_state=prev_stage,
        new_state=new_stage,
        reason=f"Score: {eval_result['final_score']} - Decision: {eval_result['decision']}"
    )

    db.commit()
    db.refresh(evaluation)
    return evaluation
