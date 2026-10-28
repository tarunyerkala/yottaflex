from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.models import (
    JobRequisition, Application, Candidate, Interview, Offer, AnomalyRecord,
    ScreeningEvaluation, Feedback, Department
)


def get_overview_metrics(db: Session) -> Dict[str, Any]:
    total_requisitions = db.query(JobRequisition).count()
    open_requisitions = db.query(JobRequisition).filter(JobRequisition.status == "Open").count()
    total_candidates = db.query(Candidate).count()
    total_applications = db.query(Application).count()

    # Screening metrics
    total_screened = db.query(ScreeningEvaluation).count()
    passed_screening = db.query(ScreeningEvaluation).filter(ScreeningEvaluation.decision == "Pass").count()
    screening_pass_rate = round((passed_screening / total_screened * 100.0), 2) if total_screened > 0 else 0.0

    # Interview metrics
    total_interviews = db.query(Interview).count()
    completed_interviews = db.query(Interview).filter(Interview.status == "Completed").count()
    interview_completion_rate = round((completed_interviews / total_interviews * 100.0), 2) if total_interviews > 0 else 0.0

    # Offer metrics
    total_offers = db.query(Offer).count()
    accepted_offers = db.query(Offer).filter(Offer.status == "Accepted").count()
    offer_acceptance_rate = round((accepted_offers / total_offers * 100.0), 2) if total_offers > 0 else 0.0

    # Active anomalies
    active_anomalies = db.query(AnomalyRecord).filter(AnomalyRecord.is_resolved == False).count()

    return {
        "total_requisitions": total_requisitions,
        "open_requisitions": open_requisitions,
        "total_candidates": total_candidates,
        "total_applications": total_applications,
        "screening_pass_rate": screening_pass_rate,
        "interview_completion_rate": interview_completion_rate,
        "offers_issued": total_offers,
        "offer_acceptance_rate": offer_acceptance_rate,
        "active_anomalies": active_anomalies
    }


def get_funnel_metrics(db: Session) -> Dict[str, Any]:
    apps_received = db.query(Application).count()
    apps_screened = db.query(Application).filter(Application.screening_decision.isnot(None)).count()
    apps_passed = db.query(Application).filter(Application.screening_decision == "Pass").count()

    # Interviewed = applications having at least one completed interview
    apps_interviewed = db.query(Application.id).join(Interview).filter(Interview.status == "Completed").distinct().count()

    # Offers = applications having an offer
    apps_offered = db.query(Application.id).join(Offer).distinct().count()

    # Hired = applications in stage Hired or offer status Accepted
    apps_hired = db.query(Application).filter(Application.stage == "Hired").count()

    return {
        "applications_received": apps_received,
        "applications_screened": apps_screened,
        "applications_passing_screening": apps_passed,
        "applications_interviewed": apps_interviewed,
        "applications_receiving_offers": apps_offered,
        "applications_hired": apps_hired
    }


def get_stage_distribution(db: Session) -> List[Dict[str, Any]]:
    results = db.query(Application.stage, func.count(Application.id)).group_by(Application.stage).all()
    return [{"stage": r[0], "count": r[1]} for r in results]


def get_department_distribution(db: Session) -> List[Dict[str, Any]]:
    results = db.query(Department.name, func.count(JobRequisition.id)).join(
        JobRequisition, JobRequisition.department_id == Department.id, isouter=True
    ).group_by(Department.name).all()
    return [{"department": r[0], "requisitions": r[1]} for r in results]


def get_exception_summary(db: Session) -> Dict[str, Any]:
    total = db.query(AnomalyRecord).count()
    unresolved = db.query(AnomalyRecord).filter(AnomalyRecord.is_resolved == False).count()

    by_category_raw = db.query(AnomalyRecord.issue_type, func.count(AnomalyRecord.id)).group_by(AnomalyRecord.issue_type).all()
    by_category = {r[0]: r[1] for r in by_category_raw}

    by_severity_raw = db.query(AnomalyRecord.severity, func.count(AnomalyRecord.id)).group_by(AnomalyRecord.severity).all()
    by_severity = {r[0]: r[1] for r in by_severity_raw}

    return {
        "total_anomalies": total,
        "unresolved_anomalies": unresolved,
        "by_category": by_category,
        "by_severity": by_severity
    }
