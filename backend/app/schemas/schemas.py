from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date


# Base schema configuration
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# --- Department ---
class DepartmentBase(BaseSchema):
    department_id: str
    name: str
    code: str
    cost_center: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentRead(DepartmentBase):
    id: int
    created_at: datetime


# --- Skill ---
class SkillBase(BaseSchema):
    skill_id: str
    name: str
    category: str

class SkillCreate(SkillBase):
    pass

class SkillRead(SkillBase):
    id: int
    created_at: datetime


# --- RequisitionSkill ---
class RequisitionSkillBase(BaseSchema):
    skill_id: int
    is_mandatory: bool = True
    min_years_experience: float = 1.0
    importance_weight: float = 1.0

class RequisitionSkillCreate(RequisitionSkillBase):
    pass

class RequisitionSkillRead(RequisitionSkillBase):
    id: int
    skill_name: Optional[str] = None


# --- JobRequisition ---
class JobRequisitionBase(BaseSchema):
    requisition_id: str
    title: str
    department_id: int
    location: str
    job_description: str
    employment_type: str = "Full-time"
    openings: int = 1
    min_salary: float
    max_salary: float
    currency: str = "USD"
    min_experience_months: int = 0
    requisition_owner: str

class JobRequisitionCreate(JobRequisitionBase):
    skills: Optional[List[RequisitionSkillCreate]] = None

class JobRequisitionApprovalRequest(BaseSchema):
    approver: str
    status: str  # Approved, Rejected
    comments: Optional[str] = None

class JobRequisitionRead(JobRequisitionBase):
    id: int
    approver: Optional[str] = None
    approval_status: str
    status: str
    opening_date: Optional[date] = None
    closing_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    department_name: Optional[str] = None
    required_skills: Optional[List[str]] = None


# --- CandidateSkill ---
class CandidateSkillBase(BaseSchema):
    skill_id: int
    proficiency_level: str = "Intermediate"
    experience_months: int = 12
    evidence_source: str = "Resume"

class CandidateSkillCreate(CandidateSkillBase):
    pass

class CandidateSkillRead(CandidateSkillBase):
    id: int
    skill_name: Optional[str] = None


# --- ResumeArtifact ---
class ResumeArtifactRead(BaseSchema):
    id: int
    artifact_id: str
    file_name: str
    mime_type: str
    file_size_bytes: int
    processing_status: str
    source_method: str
    created_at: datetime


# --- Candidate ---
class CandidateBase(BaseSchema):
    candidate_id: str
    full_name: str
    email: str
    phone: str
    total_experience_months: int = 0
    current_location: str
    profile_summary: Optional[str] = None

class CandidateCreate(CandidateBase):
    skills: Optional[List[CandidateSkillCreate]] = None

class CandidateRead(CandidateBase):
    id: int
    created_at: datetime
    skills: Optional[List[CandidateSkillRead]] = None
    resumes: Optional[List[ResumeArtifactRead]] = None


# --- ScreeningRule ---
class ScreeningRuleBase(BaseSchema):
    rule_id: str
    name: str
    description: str
    applicable_job_family: str = "All"
    criterion: str = "SkillCoverageAndExperience"
    skill_weight: float = 0.6
    experience_weight: float = 0.4
    pass_threshold: float = 70.0
    rule_version: str = "v1.0"
    is_enabled: bool = True
    effective_start_date: date
    effective_end_date: Optional[date] = None

class ScreeningRuleCreate(ScreeningRuleBase):
    pass

class ScreeningRuleRead(ScreeningRuleBase):
    id: int


# --- ScreeningEvaluation ---
class ScreeningEvaluationRead(BaseSchema):
    id: int
    evaluation_id: str
    application_id: int
    rule_version: str
    matched_skills_count: int
    total_required_skills: int
    skill_coverage_pct: float
    candidate_experience_months: int
    required_experience_months: int
    experience_score: float
    final_score: float
    decision: str
    explanation: str
    evaluated_at: datetime


# --- ApplicationStageHistory ---
class ApplicationStageHistoryRead(BaseSchema):
    id: int
    history_id: str
    from_stage: str
    to_stage: str
    actor: str
    reason: Optional[str] = None
    event_id: Optional[str] = None
    created_at: datetime


# --- Application ---
class ApplicationBase(BaseSchema):
    candidate_id: int
    requisition_id: int
    source: str = "Career Site"

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationTransitionRequest(BaseSchema):
    target_stage: str
    actor: str = "System"
    reason: Optional[str] = None

class ApplicationRead(BaseSchema):
    id: int
    application_id: str
    candidate_id: int
    requisition_id: int
    application_date: datetime
    source: str
    stage: str
    status: str
    screening_score: Optional[float] = None
    screening_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    is_duplicate: bool = False
    created_at: datetime
    updated_at: datetime
    candidate_name: Optional[str] = None
    requisition_title: Optional[str] = None


# --- Interviewer ---
class InterviewerBase(BaseSchema):
    interviewer_id: str
    full_name: str
    email: str
    department_id: int
    expertise_areas: Optional[str] = None
    is_active: bool = True

class InterviewerCreate(InterviewerBase):
    pass

class InterviewerRead(InterviewerBase):
    id: int
    created_at: datetime
    department_name: Optional[str] = None


# --- InterviewerAvailability ---
class InterviewerAvailabilityBase(BaseSchema):
    interviewer_id: int
    day_of_week: int
    start_time: str = "09:00"
    end_time: str = "17:00"
    specific_date: Optional[date] = None
    is_available: bool = True

class InterviewerAvailabilityCreate(InterviewerAvailabilityBase):
    pass

class InterviewerAvailabilityRead(InterviewerAvailabilityBase):
    id: int
    availability_id: str


# --- Interview ---
class InterviewCreate(BaseSchema):
    application_id: int
    round_number: int = 1
    interview_type: str = "Technical Round"
    scheduled_start: datetime
    scheduled_end: datetime
    time_zone: str = "UTC"
    meeting_mode: str = "Virtual - Video"
    interviewer_ids: List[int]

class InterviewRescheduleRequest(BaseSchema):
    scheduled_start: datetime
    scheduled_end: datetime
    reason: str
    actor: str = "Coordinator"

class InterviewRead(BaseSchema):
    id: int
    interview_id: str
    application_id: int
    round_number: int
    interview_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    time_zone: str
    meeting_mode: str
    status: str
    created_at: datetime
    candidate_name: Optional[str] = None
    requisition_title: Optional[str] = None
    panel_members: Optional[List[str]] = None
    panel_details: Optional[List[dict]] = None


# --- Feedback ---
class FeedbackCreate(BaseSchema):
    interviewer_id: int
    technical_score: int = Field(..., ge=1, le=5)
    problem_solving_score: int = Field(..., ge=1, le=5)
    communication_score: int = Field(..., ge=1, le=5)
    role_competency_score: int = Field(..., ge=1, le=5)
    overall_recommendation: str  # Strongly Recommend, Recommend, Mixed, Do Not Recommend
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    comments: Optional[str] = None

class FeedbackRead(BaseSchema):
    id: int
    feedback_id: str
    interview_id: int
    interviewer_id: int
    interviewer_name: Optional[str] = None
    technical_score: int
    problem_solving_score: int
    communication_score: int
    role_competency_score: int
    overall_recommendation: str
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    comments: Optional[str] = None
    submitted_at: datetime
    status: str


# --- Offer ---
class OfferCreate(BaseSchema):
    application_id: int
    proposed_salary: float
    currency: str = "USD"
    salary_period: str = "Annual"
    proposed_start_date: date
    issue_date: date
    expiry_date: date

class OfferApprovalRequest(BaseSchema):
    approver: str
    status: str  # Approved, Rejected
    reason: Optional[str] = None

class OfferRespondRequest(BaseSchema):
    response: str  # Accepted, Declined
    reason: Optional[str] = None

class OfferRead(BaseSchema):
    id: int
    offer_id: str
    application_id: int
    proposed_salary: float
    currency: str
    salary_period: str
    proposed_start_date: date
    issue_date: date
    expiry_date: date
    status: str
    approval_status: str
    approver: Optional[str] = None
    created_at: datetime
    candidate_name: Optional[str] = None
    requisition_title: Optional[str] = None
    requisition_salary_min: Optional[float] = None
    requisition_salary_max: Optional[float] = None
    requisition_status: Optional[str] = None
    requisition_id: Optional[str] = None


# --- AuditEvent ---
class AuditEventRead(BaseSchema):
    id: int
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor: str
    timestamp: datetime
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    correlation_id: Optional[str] = None


# --- AnomalyRecord ---
class AnomalyRecordRead(BaseSchema):
    id: int
    anomaly_id: str
    issue_type: str
    entity_type: str
    entity_id: str
    severity: str
    description: str
    expected_state: str
    actual_state: str
    violated_rule: str
    detected_at: datetime
    is_resolved: bool
    resolution_notes: Optional[str] = None

class AnomalyResolveRequest(BaseSchema):
    resolution_notes: str
    actor: str = "Operations Analyst"


# --- Analytics Schemas ---
class OverviewMetrics(BaseSchema):
    total_requisitions: int
    open_requisitions: int
    total_candidates: int
    total_applications: int
    screening_pass_rate: float
    interview_completion_rate: float
    offers_issued: int
    offer_acceptance_rate: float
    active_anomalies: int

class FunnelMetrics(BaseSchema):
    applications_received: int
    applications_screened: int
    applications_passing_screening: int
    applications_interviewed: int
    applications_receiving_offers: int
    applications_hired: int

class ExceptionSummary(BaseSchema):
    total_anomalies: int
    unresolved_anomalies: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
