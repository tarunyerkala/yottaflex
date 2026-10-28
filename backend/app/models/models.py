import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    department_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), nullable=False)
    cost_center = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    requisitions = relationship("JobRequisition", back_populates="department")
    interviewers = relationship("Interviewer", back_populates="department")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # Technical, Professional, Domain
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    candidate_skills = relationship("CandidateSkill", back_populates="skill")
    requisition_skills = relationship("RequisitionSkill", back_populates="skill")


class JobRequisition(Base):
    __tablename__ = "job_requisitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    location = Column(String(100), nullable=False)
    job_description = Column(Text, nullable=False)
    employment_type = Column(String(50), nullable=False, default="Full-time")
    openings = Column(Integer, nullable=False, default=1)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    min_experience_months = Column(Integer, nullable=False, default=0)
    requisition_owner = Column(String(100), nullable=False)
    approver = Column(String(100), nullable=True)
    approval_status = Column(String(50), nullable=False, default="Draft")  # Draft, Approved, Rejected, Pending
    status = Column(String(50), nullable=False, default="Draft")  # Draft, Open, Closed, On Hold, Filled
    opening_date = Column(Date, nullable=True)
    closing_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    department = relationship("Department", back_populates="requisitions")
    applications = relationship("Application", back_populates="requisition")
    requisition_skills = relationship("RequisitionSkill", back_populates="requisition", cascade="all, delete-orphan")
    approvals = relationship("RequisitionApproval", back_populates="requisition", cascade="all, delete-orphan")


class RequisitionSkill(Base):
    __tablename__ = "requisition_skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(Integer, ForeignKey("job_requisitions.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    min_years_experience = Column(Float, nullable=False, default=1.0)
    importance_weight = Column(Float, nullable=False, default=1.0)

    requisition = relationship("JobRequisition", back_populates="requisition_skills")
    skill = relationship("Skill", back_populates="requisition_skills")

    __table_args__ = (UniqueConstraint("requisition_id", "skill_id", name="uq_req_skill"),)


class RequisitionApproval(Base):
    __tablename__ = "requisition_approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(Integer, ForeignKey("job_requisitions.id"), nullable=False)
    approver = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # Approved, Rejected, Pending
    decision_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    comments = Column(Text, nullable=True)

    requisition = relationship("JobRequisition", back_populates="approvals")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    total_experience_months = Column(Integer, nullable=False, default=0)
    current_location = Column(String(100), nullable=False)
    profile_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    candidate_skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    resumes = relationship("ResumeArtifact", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    proficiency_level = Column(String(50), nullable=False, default="Intermediate")  # Beginner, Intermediate, Advanced, Expert
    experience_months = Column(Integer, nullable=False, default=12)
    evidence_source = Column(String(100), nullable=False, default="Resume")
    last_verified_date = Column(Date, nullable=True)

    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills")

    __table_args__ = (UniqueConstraint("candidate_id", "skill_id", name="uq_cand_skill"),)


class ResumeArtifact(Base):
    __tablename__ = "resume_artifacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artifact_id = Column(String(50), unique=True, nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    file_name = Column(String(200), nullable=False)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    file_size_bytes = Column(Integer, nullable=False, default=10240)
    storage_reference = Column(String(300), nullable=False)
    processing_status = Column(String(50), nullable=False, default="Processed")
    extracted_skills = Column(Text, nullable=True)  # JSON or comma-separated
    source_method = Column(String(100), nullable=False, default="SyntheticGenerator")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="resumes")


class ScreeningRule(Base):
    __tablename__ = "screening_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    applicable_job_family = Column(String(100), nullable=False, default="All")
    criterion = Column(String(100), nullable=False, default="SkillCoverageAndExperience")
    skill_weight = Column(Float, nullable=False, default=0.6)
    experience_weight = Column(Float, nullable=False, default=0.4)
    pass_threshold = Column(Float, nullable=False, default=70.0)
    rule_version = Column(String(20), nullable=False, default="v1.0")
    is_enabled = Column(Boolean, nullable=False, default=True)
    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date, nullable=True)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(String(100), unique=True, nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    requisition_id = Column(Integer, ForeignKey("job_requisitions.id"), nullable=False)
    application_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    source = Column(String(50), nullable=False, default="Career Site")
    stage = Column(String(50), nullable=False, default="Applied")
    # Stages: Applied, Screening, Screening Passed, Screening Rejected, Interview, Interview Evaluation, Final Review, Offer Pending Approval, Offer Extended, Hired, Rejected, Withdrawn
    status = Column(String(50), nullable=False, default="Active")  # Active, Archived, Closed, Flagged
    screening_score = Column(Float, nullable=True)
    screening_decision = Column(String(20), nullable=True)  # Pass, Fail, Pending
    decision_reason = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="applications")
    requisition = relationship("JobRequisition", back_populates="applications")
    stage_history = relationship("ApplicationStageHistory", back_populates="application", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="application", cascade="all, delete-orphan")
    screening_evaluations = relationship("ScreeningEvaluation", back_populates="application", cascade="all, delete-orphan")


class ScreeningEvaluation(Base):
    __tablename__ = "screening_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluation_id = Column(String(50), unique=True, nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    rule_version = Column(String(20), nullable=False, default="v1.0")
    matched_skills_count = Column(Integer, nullable=False, default=0)
    total_required_skills = Column(Integer, nullable=False, default=0)
    skill_coverage_pct = Column(Float, nullable=False, default=0.0)
    candidate_experience_months = Column(Integer, nullable=False, default=0)
    required_experience_months = Column(Integer, nullable=False, default=0)
    experience_score = Column(Float, nullable=False, default=0.0)
    final_score = Column(Float, nullable=False, default=0.0)
    decision = Column(String(20), nullable=False)  # Pass, Fail
    explanation = Column(Text, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="screening_evaluations")


class ApplicationStageHistory(Base):
    __tablename__ = "application_stage_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    history_id = Column(String(50), unique=True, nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    from_stage = Column(String(50), nullable=False)
    to_stage = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    reason = Column(Text, nullable=True)
    event_id = Column(String(50), nullable=True)
    rule_version = Column(String(20), nullable=False, default="v1.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="stage_history")


class Interviewer(Base):
    __tablename__ = "interviewers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interviewer_id = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    expertise_areas = Column(Text, nullable=True)  # JSON string or comma-separated
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    department = relationship("Department", back_populates="interviewers")
    availabilities = relationship("InterviewerAvailability", back_populates="interviewer", cascade="all, delete-orphan")
    panel_memberships = relationship("InterviewPanelMember", back_populates="interviewer")
    feedbacks = relationship("Feedback", back_populates="interviewer")


class InterviewerAvailability(Base):
    __tablename__ = "interviewer_availabilities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    availability_id = Column(String(50), unique=True, nullable=False, index=True)
    interviewer_id = Column(Integer, ForeignKey("interviewers.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(10), nullable=False, default="09:00")
    end_time = Column(String(10), nullable=False, default="17:00")
    specific_date = Column(Date, nullable=True)  # override if specific date
    is_available = Column(Boolean, nullable=False, default=True)

    interviewer = relationship("Interviewer", back_populates="availabilities")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(String(50), unique=True, nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    round_number = Column(Integer, nullable=False, default=1)
    interview_type = Column(String(100), nullable=False)  # Technical Round, Culture Fit, etc.
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    time_zone = Column(String(50), nullable=False, default="UTC")
    meeting_mode = Column(String(50), nullable=False, default="Virtual - Video")
    status = Column(String(50), nullable=False, default="Scheduled")  # Scheduled, Completed, Cancelled, Rescheduled
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="interviews")
    panel_members = relationship("InterviewPanelMember", back_populates="interview", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="interview", cascade="all, delete-orphan")


class InterviewPanelMember(Base):
    __tablename__ = "interview_panel_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("interviewers.id"), nullable=False)
    role = Column(String(50), nullable=False, default="Lead Interviewer")  # Lead Interviewer, Panel Member

    interview = relationship("Interview", back_populates="panel_members")
    interviewer = relationship("Interviewer", back_populates="panel_memberships")

    __table_args__ = (UniqueConstraint("interview_id", "interviewer_id", name="uq_interview_panel"),)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id = Column(String(100), unique=True, nullable=False, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("interviewers.id"), nullable=False)
    technical_score = Column(Integer, nullable=False)  # 1-5
    problem_solving_score = Column(Integer, nullable=False)  # 1-5
    communication_score = Column(Integer, nullable=False)  # 1-5
    role_competency_score = Column(Integer, nullable=False)  # 1-5
    overall_recommendation = Column(String(50), nullable=False)
    # Strongly Recommend, Recommend, Mixed, Do Not Recommend
    strengths = Column(Text, nullable=True)
    concerns = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String(50), nullable=False, default="Submitted")  # Submitted, Draft, Revoked

    interview = relationship("Interview", back_populates="feedbacks")
    interviewer = relationship("Interviewer", back_populates="feedbacks")

    __table_args__ = (UniqueConstraint("interview_id", "interviewer_id", name="uq_interview_feedback"),)


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    offer_id = Column(String(50), unique=True, nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    proposed_salary = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    salary_period = Column(String(20), nullable=False, default="Annual")
    proposed_start_date = Column(Date, nullable=False)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="Draft")
    # Draft, Pending Approval, Approved, Rejected, Extended, Accepted, Declined, Expired, Withdrawn
    approval_status = Column(String(50), nullable=False, default="Pending")  # Pending, Approved, Rejected
    approver = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="offers")
    approvals = relationship("OfferApproval", back_populates="offer", cascade="all, delete-orphan")
    status_history = relationship("OfferStatusHistory", back_populates="offer", cascade="all, delete-orphan")


class OfferApproval(Base):
    __tablename__ = "offer_approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    approver = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # Approved, Rejected, Pending
    decision_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    reason = Column(Text, nullable=True)

    offer = relationship("Offer", back_populates="approvals")


class OfferStatusHistory(Base):
    __tablename__ = "offer_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    offer = relationship("Offer", back_populates="status_history")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    previous_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=True)


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    anomaly_id = Column(String(50), unique=True, nullable=False, index=True)
    issue_type = Column(String(100), nullable=False, index=True)
    # AVAILABILITY_CONFLICT, DUPLICATE_APPLICATION, MISSING_FEEDBACK_ADVANCED_STAGE,
    # SALARY_BAND_VIOLATION, CLOSED_REQUISITION_ACTIVE_APPLICATIONS
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="High")  # Low, Medium, High, Critical
    description = Column(Text, nullable=False)
    expected_state = Column(Text, nullable=False)
    actual_state = Column(Text, nullable=False)
    violated_rule = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolution_notes = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="Operations Analyst")
    # Business Requester, Process Owner, Approver, Operations Analyst, System Administrator
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
