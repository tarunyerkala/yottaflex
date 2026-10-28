import datetime
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import (
    JobRequisition, Application, Candidate, CandidateSkill,
    RequisitionSkill, ScreeningRule, Interview, InterviewPanelMember,
    Feedback, Offer, Interviewer, InterviewerAvailability
)


class BusinessRuleViolation(Exception):
    def __init__(self, message: str, rule_name: str, code: int = 400):
        self.message = message
        self.rule_name = rule_name
        self.code = code
        super().__init__(self.message)


# --- 1. Requisition Acceptance Rule ---
def validate_requisition_can_accept_application(requisition: JobRequisition):
    if requisition.approval_status != "Approved":
        raise BusinessRuleViolation(
            f"Requisition {requisition.requisition_id} is in status '{requisition.approval_status}', not 'Approved'. Applications are not accepted.",
            "REQUISITION_NOT_APPROVED",
            code=400
        )
    if requisition.status != "Open":
        raise BusinessRuleViolation(
            f"Requisition {requisition.requisition_id} is '{requisition.status}'. New applications can only be submitted to 'Open' requisitions.",
            "REQUISITION_NOT_OPEN",
            code=400
        )


# --- 2. Candidate Screening Evaluation Rule ---
def evaluate_candidate_screening(
    db: Session,
    candidate: Candidate,
    requisition: JobRequisition,
    rule: ScreeningRule
) -> Dict[str, Any]:
    # Collect required skills
    req_skills = requisition.requisition_skills
    total_required = len(req_skills)

    # Collect candidate skill IDs
    candidate_skill_ids = {cs.skill_id for cs in candidate.candidate_skills}

    matched_skills = []
    missing_skills = []
    for rs in req_skills:
        skill_name = rs.skill.name if rs.skill else f"Skill-{rs.skill_id}"
        if rs.skill_id in candidate_skill_ids:
            matched_skills.append(skill_name)
        else:
            missing_skills.append(skill_name)

    matched_count = len(matched_skills)
    skill_coverage_pct = (matched_count / total_required * 100.0) if total_required > 0 else 100.0

    # Experience normalization
    min_exp_required = requisition.min_experience_months
    candidate_exp = candidate.total_experience_months
    if min_exp_required <= 0:
        experience_score = 100.0
    else:
        experience_score = min(100.0, (candidate_exp / min_exp_required) * 100.0)

    # Weighted composite score
    skill_weight = rule.skill_weight
    exp_weight = rule.experience_weight
    final_score = round((skill_coverage_pct * skill_weight) + (experience_score * exp_weight), 2)

    decision = "Pass" if final_score >= rule.pass_threshold else "Fail"

    explanation = (
        f"Screening completed under rule {rule.rule_version} ('{rule.name}'). "
        f"Matched {matched_count}/{total_required} required skills ({skill_coverage_pct:.1f}%). "
        f"Candidate experience: {candidate_exp} months vs {min_exp_required} months required ({experience_score:.1f}%). "
        f"Weighted score: {final_score:.2f} (Skill weight: {skill_weight}, Exp weight: {exp_weight}, Threshold: {rule.pass_threshold}). "
        f"Result: {decision}."
    )

    return {
        "matched_count": matched_count,
        "total_required": total_required,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_coverage_pct": round(skill_coverage_pct, 2),
        "candidate_experience_months": candidate_exp,
        "required_experience_months": min_exp_required,
        "experience_score": round(experience_score, 2),
        "final_score": final_score,
        "decision": decision,
        "explanation": explanation,
        "rule_version": rule.rule_version
    }


# --- 3. Interview Scheduling Conflict Rules ---
def validate_interview_scheduling(
    db: Session,
    interviewer_ids: List[int],
    scheduled_start: datetime.datetime,
    scheduled_end: datetime.datetime,
    exclude_interview_id: Optional[int] = None
):
    if scheduled_start >= scheduled_end:
        raise BusinessRuleViolation(
            "Scheduled interview start time must strictly precede end time.",
            "INVALID_TIME_RANGE",
            code=400
        )

    for inv_id in interviewer_ids:
        interviewer = db.query(Interviewer).filter(Interviewer.id == inv_id).first()
        if not interviewer:
            raise BusinessRuleViolation(f"Interviewer ID {inv_id} not found.", "INTERVIEWER_NOT_FOUND", code=404)
        if not interviewer.is_active:
            raise BusinessRuleViolation(
                f"Interviewer '{interviewer.full_name}' is inactive and cannot be scheduled.",
                "INTERVIEWER_INACTIVE",
                code=400
            )

        # Check general availability window if configured
        availabilities = db.query(InterviewerAvailability).filter(
            InterviewerAvailability.interviewer_id == inv_id,
            InterviewerAvailability.is_available == True
        ).all()

        if availabilities:
            day_of_week = scheduled_start.weekday()
            start_str = scheduled_start.strftime("%H:%M")
            end_str = scheduled_end.strftime("%H:%M")

            is_in_window = False
            for avail in availabilities:
                if avail.day_of_week == day_of_week:
                    if avail.start_time <= start_str and end_str <= avail.end_time:
                        is_in_window = True
                        break
            if not is_in_window:
                raise BusinessRuleViolation(
                    f"Interviewer '{interviewer.full_name}' is not available at {start_str}-{end_str} on day {day_of_week}.",
                    "INTERVIEWER_AVAILABILITY_CONFLICT",
                    code=409
                )

        # Check double booking
        conflict_query = db.query(Interview).join(InterviewPanelMember).filter(
            InterviewPanelMember.interviewer_id == inv_id,
            Interview.status.in_(["Scheduled", "Rescheduled"]),
            Interview.scheduled_start < scheduled_end,
            Interview.scheduled_end > scheduled_start
        )
        if exclude_interview_id:
            conflict_query = conflict_query.filter(Interview.id != exclude_interview_id)

        conflicting_interview = conflict_query.first()
        if conflicting_interview:
            raise BusinessRuleViolation(
                f"Interviewer '{interviewer.full_name}' has a scheduling conflict with interview {conflicting_interview.interview_id} ({conflicting_interview.scheduled_start} to {conflicting_interview.scheduled_end}).",
                "INTERVIEWER_DOUBLE_BOOKED",
                code=409
            )


# --- 4. Feedback Rules ---
def validate_feedback_submission(
    db: Session,
    interview: Interview,
    interviewer_id: int,
    scores: Dict[str, int],
    recommendation: str
):
    valid_recommendations = ["Strongly Recommend", "Recommend", "Mixed", "Do Not Recommend"]
    if recommendation not in valid_recommendations:
        raise BusinessRuleViolation(
            f"Recommendation '{recommendation}' is invalid. Allowed: {valid_recommendations}",
            "INVALID_RECOMMENDATION",
            code=422
        )

    for metric, score in scores.items():
        if score < 1 or score > 5:
            raise BusinessRuleViolation(
                f"Feedback score for '{metric}' must be between 1 and 5. Received: {score}",
                "INVALID_SCORE_RANGE",
                code=422
            )

    # Check panel membership
    is_panel_member = db.query(InterviewPanelMember).filter(
        InterviewPanelMember.interview_id == interview.id,
        InterviewPanelMember.interviewer_id == interviewer_id
    ).first()

    if not is_panel_member:
        raise BusinessRuleViolation(
            f"Interviewer ID {interviewer_id} is not an assigned panel member for interview {interview.interview_id}.",
            "UNAUTHORIZED_INTERVIEWER_FEEDBACK",
            code=403
        )


# --- 5. Application Stage State Machine ---
VALID_STAGE_TRANSITIONS = {
    "Applied": ["Screening", "Screening Passed", "Screening Rejected", "Rejected", "Withdrawn"],
    "Screening": ["Screening Passed", "Screening Rejected", "Rejected", "Withdrawn"],
    "Screening Passed": ["Interview", "Rejected", "Withdrawn"],
    "Screening Rejected": ["Withdrawn"],
    "Interview": ["Interview Evaluation", "Final Review", "Interview Rejected", "Rejected", "Withdrawn"],
    "Interview Evaluation": ["Final Review", "Interview", "Interview Rejected", "Rejected", "Withdrawn"],
    "Interview Rejected": ["Withdrawn"],
    "Final Review": ["Offer Pending Approval", "Offer Extended", "Panel Rejected", "Rejected", "Withdrawn"],
    "Panel Rejected": ["Withdrawn"],
    "Offer Pending Approval": ["Offer Extended", "Rejected", "Withdrawn"],
    "Offer Extended": ["Hired", "Offer Rejected", "Rejected", "Withdrawn"],
    "Offer Rejected": ["Withdrawn"],
    "Hired": [],
    "Rejected": [],
    "Withdrawn": []
}

def validate_stage_transition(
    db: Session,
    application: Application,
    target_stage: str
):
    current = application.stage
    allowed = VALID_STAGE_TRANSITIONS.get(current, [])
    if target_stage not in allowed:
        raise BusinessRuleViolation(
            f"Cannot transition application from stage '{current}' to '{target_stage}'. Permitted transitions: {allowed}",
            "INVALID_STAGE_TRANSITION",
            code=400
        )

    # Specific business gate checks:
    if target_stage == "Screening Passed":
        if application.screening_decision != "Pass":
            raise BusinessRuleViolation(
                f"Application {application.application_id} cannot advance to 'Screening Passed' because screening decision is '{application.screening_decision}'.",
                "SCREENING_DECISION_FAILED",
                code=400
            )

    if target_stage == "Final Review":
        # Must have completed interviews and all panel members must have submitted feedback!
        interviews = application.interviews
        if not interviews:
            raise BusinessRuleViolation(
                f"Application {application.application_id} has no interviews scheduled. Cannot advance to Final Review.",
                "NO_INTERVIEWS_SCHEDULED",
                code=400
            )
        for intv in interviews:
            if intv.status != "Completed":
                raise BusinessRuleViolation(
                    f"Interview {intv.interview_id} is currently '{intv.status}', not 'Completed'.",
                    "INTERVIEW_NOT_COMPLETED",
                    code=400
                )
            # Check panel feedback completion
            panel_count = len(intv.panel_members)
            feedback_count = len(intv.feedbacks)
            if feedback_count < panel_count:
                raise BusinessRuleViolation(
                    f"Interview {intv.interview_id} is missing feedback from assigned panel members ({feedback_count}/{panel_count} submitted). Stage cannot progress.",
                    "MISSING_INTERVIEW_FEEDBACK",
                    code=400
                )

    if target_stage == "Offer Extended":
        # Requires approved offer
        active_offer = next((o for o in application.offers if o.status in ["Approved", "Pending Approval", "Draft"]), None)
        if not active_offer:
            raise BusinessRuleViolation(
                f"Application {application.application_id} does not have an active offer to extend.",
                "NO_OFFER_FOUND",
                code=400
            )
        if active_offer.approval_status != "Approved":
            raise BusinessRuleViolation(
                f"Offer {active_offer.offer_id} is in approval status '{active_offer.approval_status}'. Offer must be approved before being extended.",
                "OFFER_NOT_APPROVED",
                code=400
            )

    if target_stage == "Hired":
        accepted_offer = next((o for o in application.offers if o.status == "Accepted"), None)
        if not accepted_offer:
            raise BusinessRuleViolation(
                f"Application {application.application_id} cannot be marked 'Hired' without an accepted offer.",
                "OFFER_NOT_ACCEPTED",
                code=400
            )


# --- 6. Offer Salary Band & Eligibility Rules ---
def validate_offer_creation(
    db: Session,
    application: Application,
    proposed_salary: float,
    start_date: datetime.date,
    issue_date: datetime.date,
    expiry_date: datetime.date
):
    if application.stage not in ["Final Review", "Offer Pending Approval"]:
        raise BusinessRuleViolation(
            f"Application {application.application_id} is in stage '{application.stage}'. Offers can only be created during 'Final Review' or 'Offer Pending Approval'.",
            "APPLICATION_NOT_OFFER_ELIGIBLE",
            code=400
        )

    requisition = application.requisition
    if requisition.status != "Open":
        raise BusinessRuleViolation(
            f"Requisition {requisition.requisition_id} is '{requisition.status}'. Offers can only be extended for Open requisitions.",
            "REQUISITION_NOT_OPEN_FOR_OFFER",
            code=400
        )

    # Salary band check
    if proposed_salary < requisition.min_salary or proposed_salary > requisition.max_salary:
        raise BusinessRuleViolation(
            f"Proposed salary ${proposed_salary:,.2f} is outside the approved requisition salary band [${requisition.min_salary:,.2f} - ${requisition.max_salary:,.2f}].",
            "SALARY_BAND_VIOLATION",
            code=400
        )

    # Date check
    if expiry_date <= issue_date:
        raise BusinessRuleViolation(
            "Offer expiry date must be strictly after the issue date.",
            "INVALID_OFFER_DATES",
            code=400
        )
