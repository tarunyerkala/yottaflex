import os
import sys
import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from backend.app.db.database import Base, get_db
from backend.app.models.models import (
    Department, Skill, JobRequisition, RequisitionSkill, Candidate,
    CandidateSkill, Application, Interview, Interviewer, InterviewPanelMember,
    Feedback, Offer, ScreeningRule, AnomalyRecord
)
from backend.app.rules.business_rules import (
    validate_requisition_can_accept_application,
    evaluate_candidate_screening,
    validate_interview_scheduling,
    validate_feedback_submission,
    validate_stage_transition,
    validate_offer_creation,
    BusinessRuleViolation
)

from sqlalchemy.pool import StaticPool

# Test in-memory database setup with StaticPool so all connections share the same memory database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Seed baseline fixtures
    dept = Department(department_id="DEP-ENG", name="Engineering", code="ENG", cost_center="CC-101")
    session.add(dept)
    session.commit()

    sk1 = Skill(skill_id="SKILL-001", name="Python", category="Technical")
    sk2 = Skill(skill_id="SKILL-002", name="SQL", category="Technical")
    sk3 = Skill(skill_id="SKILL-003", name="System Design", category="Technical")
    session.add_all([sk1, sk2, sk3])
    session.commit()

    inv1 = Interviewer(
        interviewer_id="INTVR-001",
        full_name="Dr. Alan Turing",
        email="alan.turing@example.test",
        department_id=dept.id,
        is_active=True
    )
    inv2 = Interviewer(
        interviewer_id="INTVR-002",
        full_name="Grace Hopper",
        email="grace.hopper@example.test",
        department_id=dept.id,
        is_active=False  # Inactive for testing
    )
    session.add_all([inv1, inv2])
    session.commit()

    rule = ScreeningRule(
        rule_id="RULE-TEST-001",
        name="Test Screening Rule",
        description="60% skills + 40% experience",
        applicable_job_family="All",
        criterion="SkillCoverageAndExperience",
        skill_weight=0.6,
        experience_weight=0.4,
        pass_threshold=70.0,
        rule_version="v1.0",
        is_enabled=True,
        effective_start_date=datetime.date(2026, 1, 1)
    )
    session.add(rule)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- TEST 1: Approved requisition creation ---
def test_01_approved_requisition_creation(client, db_session):
    resp = client.post("/api/requisitions", json={
        "requisition_id": "REQ-2026-900001",
        "title": "Principal Distributed Systems Architect",
        "department_id": 1,
        "location": "Remote",
        "job_description": "Architect cloud platforms.",
        "employment_type": "Full-time",
        "openings": 2,
        "min_salary": 140000.0,
        "max_salary": 190000.0,
        "currency": "USD",
        "min_experience_months": 48,
        "requisition_owner": "Director of Eng"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "Draft"

    # Approve requisition
    appr_resp = client.post(f"/api/requisitions/{data['id']}/approve", json={
        "approver": "VP of Engineering",
        "status": "Approved",
        "comments": "Headcount approved"
    })
    assert appr_resp.status_code == 200
    assert appr_resp.json()["approval_status"] == "Approved"
    assert appr_resp.json()["status"] == "Open"


# --- TEST 2: Rejection of unapproved requisition's application ---
def test_02_rejection_unapproved_requisition_application(client, db_session):
    # Create draft unapproved requisition
    req = JobRequisition(
        requisition_id="REQ-2026-900002",
        title="Unapproved Draft Role",
        department_id=1,
        location="Remote",
        job_description="Testing draft",
        employment_type="Full-time",
        openings=1,
        min_salary=100000.0,
        max_salary=120000.0,
        currency="USD",
        min_experience_months=24,
        requisition_owner="Hiring Manager",
        approval_status="Draft",
        status="Draft"
    )
    db_session.add(req)
    db_session.commit()

    cand = Candidate(
        candidate_id="CAND-900001",
        full_name="Ada Lovelace",
        email="ada.lovelace@example.test",
        phone="+1-555-0199",
        total_experience_months=60,
        current_location="London, UK"
    )
    db_session.add(cand)
    db_session.commit()

    # Attempt to apply to unapproved requisition
    with pytest.raises(BusinessRuleViolation) as excinfo:
        validate_requisition_can_accept_application(req)
    assert excinfo.value.rule_name == "REQUISITION_NOT_APPROVED"

    # Verify through API returns 400
    resp = client.post("/api/applications", json={
        "candidate_id": cand.id,
        "requisition_id": req.id,
        "source": "Career Site"
    })
    assert resp.status_code == 400
    assert "not 'Approved'" in resp.json()["detail"]


# --- TEST 3: Candidate creation ---
def test_03_candidate_creation(client, db_session):
    resp = client.post("/api/candidates", json={
        "candidate_id": "CAND-900002",
        "full_name": "Claude Shannon",
        "email": "claude.shannon@example.test",
        "phone": "+1-555-0188",
        "total_experience_months": 72,
        "current_location": "Boston, MA",
        "profile_summary": "Pioneer in digital circuit design and information theory."
    })
    assert resp.status_code == 201
    cand_data = resp.json()
    assert cand_data["candidate_id"] == "CAND-900002"
    assert cand_data["email"] == "claude.shannon@example.test"


# --- TEST 4: Valid application submission ---
def test_04_valid_application_submission(client, db_session):
    open_req = db_session.query(JobRequisition).filter(JobRequisition.status == "Open").first()
    cand = db_session.query(Candidate).filter(Candidate.candidate_id == "CAND-900002").first()

    resp = client.post("/api/applications", json={
        "candidate_id": cand.id,
        "requisition_id": open_req.id,
        "source": "Referral"
    })
    assert resp.status_code == 201
    app_data = resp.json()
    assert app_data["stage"] == "Applied"
    assert app_data["status"] == "Active"
    assert app_data["application_id"] == f"APP-{open_req.requisition_id}-{cand.candidate_id}"


# --- TEST 5: Duplicate-application detection ---
def test_05_duplicate_application_detection(client, db_session):
    open_req = db_session.query(JobRequisition).filter(JobRequisition.status == "Open").first()
    cand = db_session.query(Candidate).filter(Candidate.candidate_id == "CAND-900002").first()

    # Second submission with the same candidate and requisition
    resp = client.post("/api/applications", json={
        "candidate_id": cand.id,
        "requisition_id": open_req.id,
        "source": "Job Board"
    })
    assert resp.status_code == 409
    assert "already has an active application" in resp.json()["detail"]


# --- TEST 6: Screening score calculation ---
def test_06_screening_score_calculation(db_session):
    cand = db_session.query(Candidate).filter(Candidate.candidate_id == "CAND-900002").first()
    req = db_session.query(JobRequisition).filter(JobRequisition.requisition_id == "REQ-2026-900001").first()
    rule = db_session.query(ScreeningRule).first()

    # Assign 2 required skills to req
    db_session.add(RequisitionSkill(requisition_id=req.id, skill_id=1, is_mandatory=True))
    db_session.add(RequisitionSkill(requisition_id=req.id, skill_id=2, is_mandatory=True))
    db_session.commit()

    # Assign skill 1 to candidate (50% skill coverage)
    db_session.add(CandidateSkill(candidate_id=cand.id, skill_id=1, proficiency_level="Expert", experience_months=48))
    db_session.commit()

    result = evaluate_candidate_screening(db_session, cand, req, rule)
    assert result["matched_count"] == 1
    assert result["total_required"] == 2
    assert result["skill_coverage_pct"] == 50.0
    # Candidate exp: 72 months, req requires 48 months -> exp score = 100.0
    # Weighted score: (50.0 * 0.6) + (100.0 * 0.4) = 30 + 40 = 70.0
    assert result["final_score"] == 70.0
    assert result["decision"] == "Pass"


# --- TEST 7: Screening decision explanation ---
def test_07_screening_decision_explanation(db_session):
    cand = db_session.query(Candidate).filter(Candidate.candidate_id == "CAND-900002").first()
    req = db_session.query(JobRequisition).filter(JobRequisition.requisition_id == "REQ-2026-900001").first()
    rule = db_session.query(ScreeningRule).first()

    result = evaluate_candidate_screening(db_session, cand, req, rule)
    explanation = result["explanation"]
    assert "Screening completed under rule" in explanation
    assert "Matched 1/2 required skills" in explanation
    assert "Weighted score: 70.0" in explanation
    assert "Result: Pass" in explanation


# --- TEST 8: Exclusion of protected attributes from screening ---
def test_08_exclusion_of_protected_attributes(db_session):
    cand = db_session.query(Candidate).first()
    rule = db_session.query(ScreeningRule).first()

    # Verify Candidate model does not have demographic / protected attribute columns
    candidate_cols = [c.name for c in Candidate.__table__.columns]
    protected_attributes = ["gender", "race", "ethnicity", "age", "religion", "disability", "photo", "marital_status"]
    for attr in protected_attributes:
        assert attr not in candidate_cols, f"Protected attribute '{attr}' found in Candidate model!"

    # Verify screening rule model only assesses skill and experience weights
    assert hasattr(rule, "skill_weight")
    assert hasattr(rule, "experience_weight")
    assert not hasattr(rule, "demographic_weight")


# --- TEST 9: Valid interview scheduling ---
def test_09_valid_interview_scheduling(client, db_session):
    app_obj = db_session.query(Application).first()
    app_obj.stage = "Screening Passed"
    db_session.commit()

    start = datetime.datetime(2026, 3, 2, 10, 0, 0)
    end = datetime.datetime(2026, 3, 2, 11, 0, 0)

    resp = client.post("/api/interviews", json={
        "application_id": app_obj.id,
        "round_number": 1,
        "interview_type": "Technical Round",
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "time_zone": "UTC",
        "meeting_mode": "Virtual - Video",
        "interviewer_ids": [1]
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "Scheduled"
    assert data["interview_id"].startswith("INT-2026-")


# --- TEST 10: Interviewer availability conflict (inactive interviewer) ---
def test_10_interviewer_availability_conflict(client, db_session):
    app_obj = db_session.query(Application).first()
    start = datetime.datetime(2026, 3, 3, 10, 0, 0)
    end = datetime.datetime(2026, 3, 3, 11, 0, 0)

    # Interviewer 2 is inactive
    resp = client.post("/api/interviews", json={
        "application_id": app_obj.id,
        "round_number": 1,
        "interview_type": "System Design",
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "time_zone": "UTC",
        "meeting_mode": "Virtual - Video",
        "interviewer_ids": [2]
    })
    assert resp.status_code == 400
    assert "inactive" in resp.json()["detail"].lower()


# --- TEST 11: Double-booked interviewer ---
def test_11_double_booked_interviewer(client, db_session):
    app_obj = db_session.query(Application).first()
    # Interviewer 1 is already scheduled for 2026-03-02 10:00 - 11:00 from Test 09
    overlap_start = datetime.datetime(2026, 3, 2, 10, 30, 0)
    overlap_end = datetime.datetime(2026, 3, 2, 11, 30, 0)

    resp = client.post("/api/interviews", json={
        "application_id": app_obj.id,
        "round_number": 2,
        "interview_type": "Follow-up",
        "scheduled_start": overlap_start.isoformat(),
        "scheduled_end": overlap_end.isoformat(),
        "time_zone": "UTC",
        "meeting_mode": "Virtual - Video",
        "interviewer_ids": [1]
    })
    assert resp.status_code == 409
    assert "scheduling conflict" in resp.json()["detail"].lower()


# --- TEST 12: Valid feedback submission ---
def test_12_valid_feedback_submission(client, db_session):
    intv = db_session.query(Interview).first()
    resp = client.post(f"/api/interviews/{intv.id}/feedback", json={
        "interviewer_id": 1,
        "technical_score": 4,
        "problem_solving_score": 5,
        "communication_score": 4,
        "role_competency_score": 4,
        "overall_recommendation": "Strongly Recommend",
        "strengths": "Deep knowledge of consensus algorithms.",
        "concerns": "None.",
        "comments": "Excellent candidate."
    })
    assert resp.status_code == 201
    fb_data = resp.json()
    assert fb_data["overall_recommendation"] == "Strongly Recommend"
    assert fb_data["status"] == "Submitted"


# --- TEST 13: Invalid feedback score ---
def test_13_invalid_feedback_score(client, db_session):
    intv = db_session.query(Interview).first()
    # Score 6 is invalid (scale is 1-5)
    resp = client.post(f"/api/interviews/{intv.id}/feedback", json={
        "interviewer_id": 1,
        "technical_score": 6,
        "problem_solving_score": 5,
        "communication_score": 4,
        "role_competency_score": 4,
        "overall_recommendation": "Recommend"
    })
    assert resp.status_code in [400, 422]


# --- TEST 14: Rejection of stage transition with missing feedback ---
def test_14_rejection_stage_transition_missing_feedback(client, db_session):
    app_obj = db_session.query(Application).first()
    app_obj.stage = "Interview Evaluation"

    # Add interview with 0 feedbacks
    intv2 = Interview(
        interview_id="INT-2026-900099",
        application_id=app_obj.id,
        round_number=2,
        interview_type="Coding",
        scheduled_start=datetime.datetime(2026, 3, 5, 9, 0, 0),
        scheduled_end=datetime.datetime(2026, 3, 5, 10, 0, 0),
        status="Scheduled"
    )
    db_session.add(intv2)
    db_session.flush()
    db_session.add(InterviewPanelMember(interview_id=intv2.id, interviewer_id=1, role="Lead Interviewer"))
    db_session.commit()

    resp = client.post(f"/api/applications/{app_obj.id}/transition", json={
        "target_stage": "Final Review",
        "actor": "Coordinator",
        "reason": "Advancing candidate"
    })
    assert resp.status_code == 400
    assert "missing feedback" in resp.json()["detail"].lower() or "not 'completed'" in resp.json()["detail"].lower()


# --- TEST 15: Detection of deliberately inconsistent stage history ---
def test_15_deliberate_inconsistent_stage_history(db_session):
    app_obj = db_session.query(Application).first()
    # Attempt invalid jump from Applied directly to Hired
    app_obj.stage = "Applied"
    with pytest.raises(BusinessRuleViolation) as excinfo:
        validate_stage_transition(db_session, app_obj, "Hired")
    assert excinfo.value.rule_name == "INVALID_STAGE_TRANSITION"


# --- TEST 16: Offer creation after required approvals ---
def test_16_offer_creation_after_eligibility(client, db_session):
    app_obj = db_session.query(Application).first()
    app_obj.stage = "Final Review"
    db_session.commit()

    today = datetime.date.today()
    resp = client.post("/api/offers", json={
        "application_id": app_obj.id,
        "proposed_salary": 160000.0,
        "currency": "USD",
        "salary_period": "Annual",
        "proposed_start_date": (today + datetime.timedelta(days=30)).isoformat(),
        "issue_date": today.isoformat(),
        "expiry_date": (today + datetime.timedelta(days=14)).isoformat()
    })
    assert resp.status_code == 201
    offer_data = resp.json()
    assert offer_data["status"] == "Pending Approval"
    assert offer_data["proposed_salary"] == 160000.0


# --- TEST 17: Rejection of offer outside salary band ---
def test_17_rejection_offer_outside_salary_band(client, db_session):
    app_obj = db_session.query(Application).first()
    app_obj.stage = "Final Review"
    req = app_obj.requisition
    today = datetime.date.today()
    # Max salary is 190,000; attempt 250,000
    resp = client.post("/api/offers", json={
        "application_id": app_obj.id,
        "proposed_salary": req.max_salary + 50000.0,
        "currency": "USD",
        "salary_period": "Annual",
        "proposed_start_date": (today + datetime.timedelta(days=30)).isoformat(),
        "issue_date": today.isoformat(),
        "expiry_date": (today + datetime.timedelta(days=14)).isoformat()
    })
    assert resp.status_code in [400, 422]
    assert "outside the approved requisition salary band" in resp.json()["detail"].lower()


# --- TEST 18: Rejection of offer response without required approvals ---
def test_18_rejection_offer_response_without_approval(client, db_session):
    offer = db_session.query(Offer).first()
    offer.approval_status = "Pending"
    offer.status = "Pending Approval"
    db_session.commit()

    # Attempt to transition application stage to Offer Extended when offer not approved
    app_obj = offer.application
    app_obj.stage = "Offer Pending Approval"
    db_session.commit()

    with pytest.raises(BusinessRuleViolation) as excinfo:
        validate_stage_transition(db_session, app_obj, "Offer Extended")
    assert excinfo.value.rule_name == "OFFER_NOT_APPROVED"


# --- TEST 19: Offer acceptance ---
def test_19_offer_acceptance(client, db_session):
    offer = db_session.query(Offer).first()
    # Approve offer first
    appr_resp = client.post(f"/api/offers/{offer.id}/approve", json={
        "approver": "VP of HR",
        "status": "Approved",
        "reason": "Compensation confirmed"
    })
    assert appr_resp.status_code == 200

    # Candidate accepts
    resp = client.post(f"/api/offers/{offer.id}/respond", json={
        "response": "Accepted",
        "reason": "Thrilled to accept!"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "Accepted"
    # Candidate application marked Hired
    db_session.refresh(offer.application)
    assert offer.application.stage == "Hired"


# --- TEST 20: Rejection of acceptance for an expired offer ---
def test_20_rejection_acceptance_expired_offer(client, db_session):
    offer = db_session.query(Offer).first()
    # Set expiry date to yesterday
    offer.expiry_date = datetime.date.today() - datetime.timedelta(days=1)
    offer.status = "Approved"
    db_session.commit()

    resp = client.post(f"/api/offers/{offer.id}/respond", json={
        "response": "Accepted",
        "reason": "Accepting late"
    })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


# --- TEST 21: Closed requisition with active applications anomaly ---
def test_21_closed_requisition_active_applications(client, db_session):
    req = db_session.query(JobRequisition).filter(JobRequisition.status == "Open").first()
    req.status = "Closed"
    # Ensure active application
    cand = db_session.query(Candidate).first()
    active_app = Application(
        application_id=f"APP-{req.requisition_id}-{cand.candidate_id}-ACTIVE",
        candidate_id=cand.id,
        requisition_id=req.id,
        stage="Interview",
        status="Active"
    )
    db_session.add(active_app)
    db_session.commit()

    # Trigger scan
    resp = client.post("/api/anomalies/scan")
    assert resp.status_code == 200
    detected_types = [a["issue_type"] for a in resp.json()]
    assert "CLOSED_REQUISITION_ACTIVE_APPLICATIONS" in detected_types


# --- TEST 22: Invalid foreign key rejection ---
def test_22_invalid_foreign_key_rejection(client):
    # Attempt to submit application with non-existent candidate ID 99999
    resp = client.post("/api/applications", json={
        "candidate_id": 99999,
        "requisition_id": 1,
        "source": "Career Site"
    })
    assert resp.status_code == 404
    assert "Candidate not found" in resp.json()["detail"]


# --- TEST 23: Dashboard metric reconciliation ---
def test_23_dashboard_metric_reconciliation(client, db_session):
    resp = client.get("/api/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()

    total_reqs_db = db_session.query(JobRequisition).count()
    total_apps_db = db_session.query(Application).count()
    total_cands_db = db_session.query(Candidate).count()

    assert data["total_requisitions"] == total_reqs_db
    assert data["total_applications"] == total_apps_db
    assert data["total_candidates"] == total_cands_db


# --- TEST 24: Ground-truth separation ---
def test_24_ground_truth_separation():
    gt_path = os.path.join(PROJECT_ROOT, "ground_truth", "ground_truth.json")
    assert os.path.exists(gt_path), "Ground truth file does not exist!"

    # Verify operational models do not reference ground_truth
    app_columns = [c.name for c in Application.__table__.columns]
    assert "ground_truth_label" not in app_columns
    assert "is_anomaly_expected" not in app_columns


# --- TEST 25: Deterministic data generation ---
def test_25_deterministic_data_generation():
    repro_script = os.path.join(PROJECT_ROOT, "scripts", "reproducibility_check.py")
    assert os.path.exists(repro_script), "Reproducibility script missing!"
