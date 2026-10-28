import os
import sys
import argparse
import random
import datetime
import json
import csv

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm import Session
from backend.app.db.database import engine, Base, SessionLocal
from backend.app.models.models import (
    Department, Skill, JobRequisition, RequisitionSkill, RequisitionApproval,
    Candidate, CandidateSkill, ResumeArtifact, ScreeningRule,
    Application, ScreeningEvaluation, ApplicationStageHistory,
    Interviewer, InterviewerAvailability, Interview, InterviewPanelMember, Feedback,
    Offer, OfferApproval, OfferStatusHistory, AuditEvent, AnomalyRecord, User
)
from backend.app.rules.business_rules import evaluate_candidate_screening

# Realistic Seed Data Pools
DEPARTMENTS_DATA = [
    ("DEP-ENG", "Engineering", "ENG", "CC-1001"),
    ("DEP-PROD", "Product Management", "PROD", "CC-1002"),
    ("DEP-DES", "Product Design", "DES", "CC-1003"),
    ("DEP-DATA", "Data Science & AI", "DATA", "CC-1004"),
    ("DEP-QA", "Quality Assurance", "QA", "CC-1005"),
    ("DEP-SEC", "Information Security", "SEC", "CC-1006"),
    ("DEP-OPS", "DevOps & Cloud Infrastructure", "OPS", "CC-1007"),
    ("DEP-MKTG", "Marketing & Growth", "MKTG", "CC-2001"),
    ("DEP-SALES", "Enterprise Sales", "SALES", "CC-2002"),
    ("DEP-PEOPLE", "People Operations & HR", "HR", "CC-3001")
]

SKILLS_DATA = [
    ("Python", "Technical"),
    ("JavaScript", "Technical"),
    ("TypeScript", "Technical"),
    ("React", "Technical"),
    ("FastAPI", "Technical"),
    ("SQL", "Technical"),
    ("PostgreSQL", "Technical"),
    ("Docker", "Technical"),
    ("Kubernetes", "Technical"),
    ("AWS", "Technical"),
    ("System Design", "Technical"),
    ("Data Analysis", "Technical"),
    ("Machine Learning", "Technical"),
    ("GraphQL", "Technical"),
    ("Automated Testing", "Technical"),
    ("CI/CD Pipelines", "Technical"),
    ("Agile Methodology", "Professional"),
    ("Technical Communication", "Professional"),
    ("Problem Solving", "Professional"),
    ("Stakeholder Management", "Professional"),
    ("Product Strategy", "Domain"),
    ("UI/UX Design", "Domain"),
    ("User Research", "Domain"),
    ("Data Modeling", "Domain"),
    ("Distributed Systems", "Technical")
]

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Jamie", "Logan", "Cameron",
    "Sam", "Dakota", "Reese", "Harper", "Rowan", "Finley", "Hayden", "Emerson", "Peyton", "Kendall",
    "Arjun", "Priya", "Rohan", "Ananya", "Vikram", "Sneha", "Aditya", "Neha", "Rahul", "Pooja",
    "Chen", "Wei", "Li", "Fang", "Yan", "Jun", "Hao", "Mei", "Lin", "Feng",
    "Elena", "Mateo", "Sofia", "Lucas", "Isabella", "Gabriel", "Camila", "Diego", "Valentina", "Nicolas"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Patel", "Sharma", "Verma", "Rao", "Gupta", "Mehta", "Iyer", "Nair", "Reddy", "Choudhury",
    "Zhang", "Wang", "Li", "Zhao", "Chen", "Liu", "Yang", "Huang", "Wu", "Xu"
]

LOCATIONS = [
    "Remote, US", "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA",
    "Boston, MA", "Chicago, IL", "Denver, CO", "Atlanta, GA", "Toronto, ON"
]

JOB_TITLES = [
    ("Senior Backend Engineer", 1, 130000, 175000, 48),
    ("Staff Software Engineer", 1, 160000, 220000, 72),
    ("Full Stack Developer", 1, 105000, 145000, 36),
    ("Data Platform Engineer", 4, 125000, 170000, 48),
    ("Senior Machine Learning Engineer", 4, 145000, 195000, 48),
    ("Lead Product Designer", 3, 120000, 160000, 60),
    ("Senior Product Manager", 2, 135000, 185000, 60),
    ("Principal QA Automation Engineer", 5, 115000, 155000, 60),
    ("DevOps Cloud Architect", 7, 140000, 190000, 72),
    ("Cybersecurity Operations Analyst", 6, 110000, 150000, 36)
]


def generate_synthetic_dataset(seed: int = 20261022, scale: str = "starter", db_session: Session = None):
    random.seed(seed)
    
    if scale == "full":
        target_reqs = 100
        target_candidates = 2000
        target_applications = 3000
        target_interviews = 600
        target_offers = 150
    else:  # starter
        target_reqs = 10
        target_candidates = 200
        target_applications = 300
        target_interviews = 60
        target_offers = 15

    db = db_session or SessionLocal()
    target_engine = db.get_bind()

    # Clear existing records
    Base.metadata.drop_all(bind=target_engine)
    Base.metadata.create_all(bind=target_engine)

    print(f"[*] Generating {scale.upper()} dataset with seed {seed}...")
    print(f"[*] Target Volumes: {target_reqs} Reqs, {target_candidates} Candidates, {target_applications} Apps, {target_interviews} Interviews, {target_offers} Offers.")

    # 1. Departments
    departments = []
    for dept_id, name, code, cc in DEPARTMENTS_DATA:
        d = Department(
            department_id=dept_id,
            name=name,
            code=code,
            cost_center=cc,
            created_at=datetime.datetime(2026, 1, 1, 8, 0, 0)
        )
        db.add(d)
        departments.append(d)
    db.commit()

    # 2. Skills
    skills = []
    for idx, (sname, cat) in enumerate(SKILLS_DATA, 1):
        s = Skill(
            skill_id=f"SKILL-{idx:03d}",
            name=sname,
            category=cat,
            created_at=datetime.datetime(2026, 1, 1, 8, 0, 0)
        )
        db.add(s)
        skills.append(s)
    db.commit()

    # 3. Screening Rules
    default_rule = ScreeningRule(
        rule_id="RULE-001",
        name="Standard Skill & Experience Rule",
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
    db.add(default_rule)
    db.commit()

    # 4. Interviewers & Availability
    interviewers = []
    for i in range(1, 21):
        fname = FIRST_NAMES[(i * 7) % len(FIRST_NAMES)]
        lname = LAST_NAMES[(i * 11) % len(LAST_NAMES)]
        dept = departments[i % len(departments)]
        inv = Interviewer(
            interviewer_id=f"INTVR-{i:03d}",
            full_name=f"{fname} {lname}",
            email=f"{fname.lower()}.{lname.lower()}{i}@example.test",
            department_id=dept.id,
            expertise_areas=json.dumps(["Python", "System Design", "Testing"]),
            is_active=True,
            created_at=datetime.datetime(2026, 1, 2, 9, 0, 0)
        )
        db.add(inv)
        interviewers.append(inv)
    db.commit()

    for inv in interviewers:
        for day in range(5):  # Mon-Fri
            avail = InterviewerAvailability(
                availability_id=f"AVAIL-{inv.id}-{day}",
                interviewer_id=inv.id,
                day_of_week=day,
                start_time="09:00",
                end_time="18:00",
                is_available=True
            )
            db.add(avail)
    db.commit()

    # 5. Job Requisitions & Requisition Skills
    requisitions = []
    base_date = datetime.date(2026, 1, 10)
    for i in range(1, target_reqs + 1):
        req_id = f"REQ-2026-{i:06d}"
        title_info = JOB_TITLES[(i - 1) % len(JOB_TITLES)]
        dept = departments[title_info[1] % len(departments)]
        
        # Approval and status: Most are Approved and Open
        # For Anomaly E: We close REQ-2026-000002 later
        status = "Open"
        approval_status = "Approved"
        
        req = JobRequisition(
            requisition_id=req_id,
            title=f"{title_info[0]} - Cohort {i}",
            department_id=dept.id,
            location=LOCATIONS[i % len(LOCATIONS)],
            job_description=f"Leading responsibilities for {title_info[0]} across enterprise systems.",
            employment_type="Full-time",
            openings=random.randint(1, 4),
            min_salary=float(title_info[2]),
            max_salary=float(title_info[3]),
            currency="USD",
            min_experience_months=title_info[4],
            requisition_owner=f"HiringManager_{dept.code}",
            approver=f"VP_{dept.code}",
            approval_status=approval_status,
            status=status,
            opening_date=base_date + datetime.timedelta(days=i),
            created_at=datetime.datetime.combine(base_date + datetime.timedelta(days=i), datetime.time(9, 0, 0)),
            updated_at=datetime.datetime.combine(base_date + datetime.timedelta(days=i), datetime.time(9, 0, 0))
        )
        db.add(req)
        requisitions.append(req)
    db.commit()

    # Requisition Skills & Approvals
    for req in requisitions:
        appr = RequisitionApproval(
            requisition_id=req.id,
            approver=req.approver,
            status="Approved",
            decision_date=req.created_at,
            comments="Approved per strategic headcount allocation."
        )
        db.add(appr)

        # 3 to 5 skills
        selected_skills = random.sample(skills, random.randint(3, 5))
        for sk in selected_skills:
            rs = RequisitionSkill(
                requisition_id=req.id,
                skill_id=sk.id,
                is_mandatory=True,
                min_years_experience=2.0,
                importance_weight=1.0
            )
            db.add(rs)
    db.commit()

    # 6. Candidates & Candidate Skills & Resumes
    candidates = []
    for c_idx in range(1, target_candidates + 1):
        cid = f"CAND-{c_idx:06d}"
        fname = FIRST_NAMES[(c_idx * 13) % len(FIRST_NAMES)]
        lname = LAST_NAMES[(c_idx * 17) % len(LAST_NAMES)]
        email = f"{fname.lower()}.{lname.lower()}{c_idx}@example.test"
        phone = f"+1-555-01{c_idx % 1000:03d}"
        exp = int(random.gauss(54, 24))
        exp = max(6, min(180, exp))

        cand = Candidate(
            candidate_id=cid,
            full_name=f"{fname} {lname}",
            email=email,
            phone=phone,
            total_experience_months=exp,
            current_location=LOCATIONS[c_idx % len(LOCATIONS)],
            profile_summary=f"Experienced professional specializing in high-performance computing and scalable engineering.",
            created_at=datetime.datetime(2026, 1, 15, 10, 0, 0) + datetime.timedelta(hours=c_idx % 500)
        )
        db.add(cand)
        candidates.append(cand)
    db.commit()

    # Candidate skills & Resumes
    for cand in candidates:
        cand_skills = random.sample(skills, random.randint(4, 8))
        for sk in cand_skills:
            cs = CandidateSkill(
                candidate_id=cand.id,
                skill_id=sk.id,
                proficiency_level=random.choice(["Intermediate", "Advanced", "Expert"]),
                experience_months=random.randint(1, max(1, cand.total_experience_months)),
                evidence_source="Resume",
                last_verified_date=datetime.date(2026, 1, 20)
            )
            db.add(cs)

        resume = ResumeArtifact(
            artifact_id=f"RES-{cand.candidate_id.replace('CAND-', '')}",
            candidate_id=cand.id,
            file_name=f"{cand.full_name.lower().replace(' ', '_')}_resume.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024 * random.randint(15, 45),
            storage_reference=f"synthetic_storage/resumes/{cand.candidate_id}.pdf",
            processing_status="Processed",
            source_method="SyntheticGenerator",
            created_at=cand.created_at
        )
        db.add(resume)
    db.commit()

    # 7. Applications
    applications = []
    used_pairs = set()
    app_counter = 0
    candidate_pool_idx = 0

    while app_counter < target_applications:
        cand = candidates[candidate_pool_idx % len(candidates)]
        # Pick requisition ensuring candidate hasn't applied to this requisition yet
        req_offset = (candidate_pool_idx // len(candidates))
        req = requisitions[(candidate_pool_idx + req_offset) % len(requisitions)]
        
        # If already used, advance req until finding an unapplied req
        attempts = 0
        while (cand.id, req.id) in used_pairs and attempts < len(requisitions):
            attempts += 1
            req = requisitions[(req.id - 1 + attempts) % len(requisitions)]

        used_pairs.add((cand.id, req.id))
        candidate_pool_idx += 1

        app_id = f"APP-{req.requisition_id}-{cand.candidate_id}"
        app_date = req.created_at + datetime.timedelta(days=random.randint(1, 15), hours=random.randint(1, 8))

        app = Application(
            application_id=app_id,
            candidate_id=cand.id,
            requisition_id=req.id,
            application_date=app_date,
            source=random.choice(["Career Site", "Referral", "LinkedIn", "Job Board"]),
            stage="Applied",
            status="Active",
            is_duplicate=False,
            created_at=app_date,
            updated_at=app_date
        )
        db.add(app)
        applications.append(app)
        app_counter += 1
    db.commit()

    # 8. Screening Evaluations & Stage Transitions
    print("[*] Running deterministic screening evaluations...")
    stage_history_counter = 0
    for idx, app in enumerate(applications):
        # Initial submission history
        stage_history_counter += 1
        h0 = ApplicationStageHistory(
            history_id=f"HIST-{stage_history_counter:06d}",
            application_id=app.id,
            from_stage="None",
            to_stage="Applied",
            actor="Candidate Portal",
            reason="Application submitted",
            created_at=app.application_date
        )
        db.add(h0)

        # Evaluate candidate screening deterministically
        eval_result = evaluate_candidate_screening(db, app.candidate, app.requisition, default_rule)
        
        evaluation = ScreeningEvaluation(
            evaluation_id=f"EVAL-{app.id:06d}",
            application_id=app.id,
            rule_version=default_rule.rule_version,
            matched_skills_count=eval_result["matched_count"],
            total_required_skills=eval_result["total_required"],
            skill_coverage_pct=eval_result["skill_coverage_pct"],
            candidate_experience_months=eval_result["candidate_experience_months"],
            required_experience_months=eval_result["required_experience_months"],
            experience_score=eval_result["experience_score"],
            final_score=eval_result["final_score"],
            decision=eval_result["decision"],
            explanation=eval_result["explanation"],
            evaluated_at=app.application_date + datetime.timedelta(days=1)
        )
        db.add(evaluation)

        app.screening_score = eval_result["final_score"]
        app.screening_decision = eval_result["decision"]
        app.decision_reason = eval_result["explanation"]

        if eval_result["decision"] == "Pass":
            app.stage = "Screening Passed"
        else:
            app.stage = "Screening Rejected"
        app.updated_at = app.application_date + datetime.timedelta(days=1)

        stage_history_counter += 1
        h1 = ApplicationStageHistory(
            history_id=f"HIST-{stage_history_counter:06d}",
            application_id=app.id,
            from_stage="Applied",
            to_stage=app.stage,
            actor="Automated Screening Engine",
            reason=eval_result["explanation"],
            created_at=app.application_date + datetime.timedelta(days=1)
        )
        db.add(h1)
    db.commit()

    # 9. Interviews & Panel & Feedback
    print(f"[*] Scheduling {target_interviews} interviews and feedbacks...")
    passed_apps = [a for a in applications if a.stage == "Screening Passed"]
    interviews = []
    feedbacks = []

    interview_count = 0
    while interview_count < target_interviews:
        app = passed_apps[interview_count % len(passed_apps)]
        int_id = f"INT-2026-{interview_count + 1:06d}"
        
        # Schedule time during workday
        day_offset = (interview_count // 5) + 3
        hour_slot = 9 + (interview_count % 8)
        start_time = datetime.datetime(2026, 2, 1, hour_slot, 0, 0) + datetime.timedelta(days=day_offset)
        end_time = start_time + datetime.timedelta(hours=1)

        interview = Interview(
            interview_id=int_id,
            application_id=app.id,
            round_number=1,
            interview_type="Technical Round",
            scheduled_start=start_time,
            scheduled_end=end_time,
            time_zone="UTC",
            meeting_mode="Virtual - Video",
            status="Completed",
            created_at=start_time - datetime.timedelta(days=2),
            updated_at=end_time
        )
        db.add(interview)
        db.flush()
        interviews.append(interview)

        # 2 Panel members
        inv1 = interviewers[interview_count % len(interviewers)]
        inv2 = interviewers[(interview_count + 3) % len(interviewers)]

        p1 = InterviewPanelMember(interview_id=interview.id, interviewer_id=inv1.id, role="Lead Interviewer")
        p2 = InterviewPanelMember(interview_id=interview.id, interviewer_id=inv2.id, role="Panel Member")
        db.add(p1)
        db.add(p2)

        # App stage to Interview Evaluation
        app.stage = "Interview Evaluation"
        app.updated_at = end_time

        # Generate Feedback for both interviewers
        score_base = 4 if app.screening_score >= 80 else 3
        fb1 = Feedback(
            feedback_id=f"FB-{int_id}-{inv1.interviewer_id}",
            interview_id=interview.id,
            interviewer_id=inv1.id,
            technical_score=min(5, score_base),
            problem_solving_score=min(5, score_base),
            communication_score=4,
            role_competency_score=score_base,
            overall_recommendation="Recommend" if score_base >= 3 else "Mixed",
            strengths="Clear explanation of distributed architectures and strong algorithmic depth.",
            concerns="None observed during the round.",
            comments="Demonstrated strong system competencies.",
            submitted_at=end_time + datetime.timedelta(minutes=30),
            status="Submitted"
        )
        fb2 = Feedback(
            feedback_id=f"FB-{int_id}-{inv2.interviewer_id}",
            interview_id=interview.id,
            interviewer_id=inv2.id,
            technical_score=score_base,
            problem_solving_score=score_base,
            communication_score=4,
            role_competency_score=score_base,
            overall_recommendation="Recommend",
            strengths="Strong coding discipline and structured problem-solving approach.",
            concerns="None.",
            comments="Recommended for offer consideration.",
            submitted_at=end_time + datetime.timedelta(minutes=45),
            status="Submitted"
        )
        db.add(fb1)
        db.add(fb2)
        feedbacks.append(fb1)
        feedbacks.append(fb2)

        # Transition to Final Review
        app.stage = "Final Review"
        app.updated_at = end_time + datetime.timedelta(hours=1)
        stage_history_counter += 1
        h2 = ApplicationStageHistory(
            history_id=f"HIST-{stage_history_counter:06d}",
            application_id=app.id,
            from_stage="Interview",
            to_stage="Final Review",
            actor="Panel Lead",
            reason="All panel feedback completed with positive recommendation",
            created_at=end_time + datetime.timedelta(hours=1)
        )
        db.add(h2)

        interview_count += 1
    db.commit()

    # 10. Offers & Approvals & Status History
    print(f"[*] Generating {target_offers} offers and approvals...")
    final_review_apps = [a for a in applications if a.stage == "Final Review"]
    offers = []

    for off_idx in range(1, target_offers + 1):
        app = final_review_apps[(off_idx - 1) % len(final_review_apps)]
        off_id = f"OFF-2026-{off_idx:06d}"
        req = app.requisition

        # Salary within band: midpoint
        salary = round(req.min_salary + (req.max_salary - req.min_salary) * 0.5, 2)
        issue_date = datetime.date(2026, 2, 20) + datetime.timedelta(days=off_idx % 10)
        expiry_date = issue_date + datetime.timedelta(days=14)
        start_date = issue_date + datetime.timedelta(days=30)

        # Status distribution: 60% Accepted, 20% Extended, 10% Declined, 10% Approved
        mod = off_idx % 10
        if mod in [0, 1, 2, 3, 4, 5]:
            off_status = "Accepted"
            app_stage = "Hired"
            app_status = "Closed"
        elif mod in [6, 7]:
            off_status = "Extended"
            app_stage = "Offer Extended"
            app_status = "Active"
        elif mod == 8:
            off_status = "Declined"
            app_stage = "Rejected"
            app_status = "Closed"
        else:
            off_status = "Approved"
            app_stage = "Offer Pending Approval"
            app_status = "Active"

        offer = Offer(
            offer_id=off_id,
            application_id=app.id,
            proposed_salary=salary,
            currency="USD",
            salary_period="Annual",
            proposed_start_date=start_date,
            issue_date=issue_date,
            expiry_date=expiry_date,
            status=off_status,
            approval_status="Approved",
            approver=req.approver,
            created_at=datetime.datetime.combine(issue_date, datetime.time(10, 0, 0)),
            updated_at=datetime.datetime.combine(issue_date, datetime.time(10, 0, 0))
        )
        db.add(offer)
        db.flush()
        offers.append(offer)

        app.stage = app_stage
        app.status = app_status
        app.updated_at = datetime.datetime.combine(issue_date, datetime.time(10, 0, 0))

        # Offer approval record
        appr = OfferApproval(
            offer_id=offer.id,
            approver=req.approver,
            status="Approved",
            decision_date=offer.created_at,
            reason="Candidate exceeded evaluation criteria; offer within compensation guidelines."
        )
        db.add(appr)

        # Status history
        sh1 = OfferStatusHistory(
            offer_id=offer.id,
            from_status="None",
            to_status="Approved",
            actor=req.approver,
            reason="Executive approval granted",
            changed_at=offer.created_at
        )
        db.add(sh1)
        if off_status != "Approved":
            sh2 = OfferStatusHistory(
                offer_id=offer.id,
                from_status="Approved",
                to_status=off_status,
                actor="Candidate" if off_status in ["Accepted", "Declined"] else "Recruiter",
                reason=f"Offer {off_status.lower()}",
                changed_at=offer.created_at + datetime.timedelta(days=2)
            )
            db.add(sh2)
    db.commit()

    # 11. INJECT THE 5 REQUIRED ANOMALIES & GROUND TRUTH
    print("[*] Injecting 5 required deliberate anomaly categories...")
    ground_truth_records = []

    # Anomaly A: Interviewer availability conflict / Double-booking
    # Pick interview 1 and schedule a second overlapping interview with the same interviewer
    conflicting_inv = interviewers[2]  # INTVR-003
    base_int = interviews[0]
    conflict_int = Interview(
        interview_id="INT-2026-999001",
        application_id=applications[10].id,
        round_number=2,
        interview_type="System Design",
        scheduled_start=base_int.scheduled_start,  # Exact duplicate overlapping slot
        scheduled_end=base_int.scheduled_end,
        time_zone="UTC",
        meeting_mode="Virtual - Video",
        status="Scheduled",
        created_at=datetime.datetime(2026, 2, 1, 8, 0, 0),
        updated_at=datetime.datetime(2026, 2, 1, 8, 0, 0)
    )
    db.add(conflict_int)
    db.flush()
    db.add(InterviewPanelMember(interview_id=conflict_int.id, interviewer_id=conflicting_inv.id, role="Lead Interviewer"))
    # Also add conflicting_inv to base_int panel to guarantee double-booking!
    db.add(InterviewPanelMember(interview_id=base_int.id, interviewer_id=conflicting_inv.id, role="Panel Member"))
    db.commit()

    anom_a = AnomalyRecord(
        anomaly_id="ANOM-A-001",
        issue_type="AVAILABILITY_CONFLICT",
        entity_type="Interview",
        entity_id=conflict_int.interview_id,
        severity="High",
        description=f"Interviewer {conflicting_inv.full_name} is double-booked between {base_int.interview_id} and {conflict_int.interview_id}.",
        expected_state="Interviewer has non-overlapping, available schedule slots",
        actual_state=f"Overlapping schedule at {base_int.scheduled_start}",
        violated_rule="INTERVIEWER_DOUBLE_BOOKED",
        detected_at=datetime.datetime(2026, 2, 25, 12, 0, 0),
        is_resolved=False
    )
    db.add(anom_a)
    ground_truth_records.append({
        "anomaly_id": "ANOM-A-001",
        "issue_type": "AVAILABILITY_CONFLICT",
        "entity_type": "Interview",
        "affected_business_ids": f"{conflict_int.interview_id}, {base_int.interview_id}, {conflicting_inv.interviewer_id}",
        "expected_outcome": "Conflict detected during scheduling audit",
        "actual_observed_condition": "Two active interviews overlap exactly on the same interviewer schedule",
        "violated_business_rule": "INTERVIEWER_DOUBLE_BOOKED",
        "expected_detection_result": "DETECTED",
        "severity": "High",
        "detection_rationale": "Scheduling an interviewer for concurrent slots violates interview availability constraint."
    })

    # Anomaly B: Duplicate candidate application
    # Pick a candidate and requisition and insert duplicate application record
    dup_cand = candidates[4]
    dup_req = requisitions[2]
    dup_app = Application(
        application_id=f"APP-{dup_req.requisition_id}-{dup_cand.candidate_id}-DUP",
        candidate_id=dup_cand.id,
        requisition_id=dup_req.id,
        application_date=datetime.datetime(2026, 1, 22, 14, 0, 0),
        source="LinkedIn",
        stage="Applied",
        status="Active",
        is_duplicate=True,
        created_at=datetime.datetime(2026, 1, 22, 14, 0, 0),
        updated_at=datetime.datetime(2026, 1, 22, 14, 0, 0)
    )
    db.add(dup_app)
    db.commit()

    anom_b = AnomalyRecord(
        anomaly_id="ANOM-B-001",
        issue_type="DUPLICATE_APPLICATION",
        entity_type="Application",
        entity_id=dup_app.application_id,
        severity="Medium",
        description=f"Duplicate submission detected for candidate {dup_cand.candidate_id} on requisition {dup_req.requisition_id}.",
        expected_state="Candidate should have exactly one active application per requisition",
        actual_state="Multiple active submissions preserved in database",
        violated_rule="DUPLICATE_APPLICATION_POLICY",
        detected_at=datetime.datetime(2026, 2, 25, 12, 0, 0),
        is_resolved=False
    )
    db.add(anom_b)
    ground_truth_records.append({
        "anomaly_id": "ANOM-B-001",
        "issue_type": "DUPLICATE_APPLICATION",
        "entity_type": "Application",
        "affected_business_ids": f"{dup_app.application_id}, {dup_cand.candidate_id}, {dup_req.requisition_id}",
        "expected_outcome": "Duplicate application identified and flagged",
        "actual_observed_condition": "Candidate submitted second application to the same requisition",
        "violated_business_rule": "DUPLICATE_APPLICATION_POLICY",
        "expected_detection_result": "DETECTED",
        "severity": "Medium",
        "detection_rationale": "Candidates may not have multiple concurrent applications for the same job requisition."
    })

    # Anomaly C: Missing feedback but advanced stage
    # Create an application that reached Offer Pending Approval, but its interview has 0 feedbacks
    c_app = applications[15]
    c_int = Interview(
        interview_id="INT-2026-999002",
        application_id=c_app.id,
        round_number=1,
        interview_type="Technical Round",
        scheduled_start=datetime.datetime(2026, 2, 5, 10, 0, 0),
        scheduled_end=datetime.datetime(2026, 2, 5, 11, 0, 0),
        time_zone="UTC",
        meeting_mode="Virtual - Video",
        status="Scheduled",  # Never completed and no feedback!
        created_at=datetime.datetime(2026, 2, 1, 10, 0, 0),
        updated_at=datetime.datetime(2026, 2, 1, 10, 0, 0)
    )
    db.add(c_int)
    db.flush()
    db.add(InterviewPanelMember(interview_id=c_int.id, interviewer_id=interviewers[0].id, role="Lead Interviewer"))
    c_app.stage = "Final Review"  # Advanced despite missing feedback!
    c_app.updated_at = datetime.datetime(2026, 2, 5, 12, 0, 0)
    db.commit()

    anom_c = AnomalyRecord(
        anomaly_id="ANOM-C-001",
        issue_type="MISSING_FEEDBACK_ADVANCED_STAGE",
        entity_type="Application",
        entity_id=c_app.application_id,
        severity="High",
        description=f"Application {c_app.application_id} advanced to stage '{c_app.stage}' while interview {c_int.interview_id} had 0 feedbacks submitted.",
        expected_state="Application cannot advance to Final Review without all panel feedback",
        actual_state="Application is in Final Review with 0/1 feedbacks",
        violated_rule="STAGE_PROGRESSION_FEEDBACK_GATE",
        detected_at=datetime.datetime(2026, 2, 25, 12, 0, 0),
        is_resolved=False
    )
    db.add(anom_c)
    ground_truth_records.append({
        "anomaly_id": "ANOM-C-001",
        "issue_type": "MISSING_FEEDBACK_ADVANCED_STAGE",
        "entity_type": "Application",
        "affected_business_ids": f"{c_app.application_id}, {c_int.interview_id}",
        "expected_outcome": "Stage progression policy violation detected",
        "actual_observed_condition": "Application stage advanced to Final Review without completed panel feedback",
        "violated_business_rule": "STAGE_PROGRESSION_FEEDBACK_GATE",
        "expected_detection_result": "DETECTED",
        "severity": "High",
        "detection_rationale": "Advancing a candidate without required panel feedback violates hiring governance."
    })

    # Anomaly D: Offer outside approved salary band
    # Create an offer whose salary is $250,000 when requisition max is $175,000
    target_d_app = applications[8]
    req_d = target_d_app.requisition
    excessive_salary = req_d.max_salary + 45000.0  # Deliberately out of band

    d_offer = Offer(
        offer_id="OFF-2026-999001",
        application_id=target_d_app.id,
        proposed_salary=excessive_salary,
        currency="USD",
        salary_period="Annual",
        proposed_start_date=datetime.date(2026, 3, 1),
        issue_date=datetime.date(2026, 2, 10),
        expiry_date=datetime.date(2026, 2, 24),
        status="Approved",
        approval_status="Approved",
        approver=req_d.approver,
        created_at=datetime.datetime(2026, 2, 10, 11, 0, 0),
        updated_at=datetime.datetime(2026, 2, 10, 11, 0, 0)
    )
    db.add(d_offer)
    db.commit()

    anom_d = AnomalyRecord(
        anomaly_id="ANOM-D-001",
        issue_type="SALARY_BAND_VIOLATION",
        entity_type="Offer",
        entity_id=d_offer.offer_id,
        severity="Critical",
        description=f"Offer {d_offer.offer_id} has proposed salary ${excessive_salary:,.2f}, which is outside approved band [${req_d.min_salary:,.2f} - ${req_d.max_salary:,.2f}].",
        expected_state=f"Proposed salary within approved band [${req_d.min_salary:,.2f} - ${req_d.max_salary:,.2f}]",
        actual_state=f"Proposed salary is ${excessive_salary:,.2f}",
        violated_rule="SALARY_BAND_APPROVAL_LIMIT",
        detected_at=datetime.datetime(2026, 2, 25, 12, 0, 0),
        is_resolved=False
    )
    db.add(anom_d)
    ground_truth_records.append({
        "anomaly_id": "ANOM-D-001",
        "issue_type": "SALARY_BAND_VIOLATION",
        "entity_type": "Offer",
        "affected_business_ids": f"{d_offer.offer_id}, {req_d.requisition_id}",
        "expected_outcome": "Compensation band violation flagged",
        "actual_observed_condition": f"Proposed salary ${excessive_salary} exceeds maximum ${req_d.max_salary}",
        "violated_business_rule": "SALARY_BAND_APPROVAL_LIMIT",
        "expected_detection_result": "DETECTED",
        "severity": "Critical",
        "detection_rationale": "Offers outside the approved requisition band must not be generated without band adjustments."
    })

    # Anomaly E: Closed requisition with active applications
    closed_req = requisitions[1]  # REQ-2026-000002
    closed_req.status = "Closed"
    closed_req.closing_date = datetime.date(2026, 2, 15)
    closed_req.updated_at = datetime.datetime(2026, 2, 15, 12, 0, 0)
    db.commit()

    # Active applications remain attached to this closed req!
    anom_e = AnomalyRecord(
        anomaly_id="ANOM-E-001",
        issue_type="CLOSED_REQUISITION_ACTIVE_APPLICATIONS",
        entity_type="JobRequisition",
        entity_id=closed_req.requisition_id,
        severity="High",
        description=f"Requisition {closed_req.requisition_id} is Closed but has active applications pending explicit disposition.",
        expected_state="All applications must be resolved (Hired, Rejected, Withdrawn) prior to closing requisition",
        actual_state=f"Requisition {closed_req.requisition_id} is Closed with active candidate pipelines",
        violated_rule="REQUISITION_DISPOSITION_POLICY",
        detected_at=datetime.datetime(2026, 2, 25, 12, 0, 0),
        is_resolved=False
    )
    db.add(anom_e)
    ground_truth_records.append({
        "anomaly_id": "ANOM-E-001",
        "issue_type": "CLOSED_REQUISITION_ACTIVE_APPLICATIONS",
        "entity_type": "JobRequisition",
        "affected_business_ids": f"{closed_req.requisition_id}",
        "expected_outcome": "Closed requisition active pipeline violation flagged",
        "actual_observed_condition": "Requisition marked Closed while applications remain active",
        "violated_business_rule": "REQUISITION_DISPOSITION_POLICY",
        "expected_detection_result": "DETECTED",
        "severity": "High",
        "detection_rationale": "Closing a requisition without disposing of in-flight applications leaves candidates stranded."
    })
    # 12. Audit Events Generation
    print("[*] Generating audit event history records...")
    audit_counter = 0

    # Requisition audit events
    for req in requisitions:
        audit_counter += 1
        db.add(AuditEvent(
            event_id=f"AUD-REQ-{audit_counter:06d}",
            event_type="REQUISITION_CREATED",
            entity_type="JobRequisition",
            entity_id=req.requisition_id,
            actor=req.requisition_owner,
            timestamp=req.created_at,
            previous_state=None,
            new_state="Draft",
            reason="Headcount requisition initiated",
            correlation_id=f"CORR-{req.requisition_id}"
        ))
        if req.approval_status == "Approved":
            audit_counter += 1
            db.add(AuditEvent(
                event_id=f"AUD-REQ-{audit_counter:06d}",
                event_type="REQUISITION_APPROVED",
                entity_type="JobRequisition",
                entity_id=req.requisition_id,
                actor=req.approver or "System",
                timestamp=req.created_at,
                previous_state="Draft",
                new_state="Approved",
                reason="Strategic headcount approved",
                correlation_id=f"CORR-{req.requisition_id}"
            ))

    # Application & Screening audit events
    for app in applications:
        audit_counter += 1
        db.add(AuditEvent(
            event_id=f"AUD-APP-{audit_counter:06d}",
            event_type="APPLICATION_SUBMITTED",
            entity_type="Application",
            entity_id=app.application_id,
            actor="Candidate Portal",
            timestamp=app.application_date,
            previous_state=None,
            new_state="Applied",
            reason=f"Candidate applied via {app.source}",
            correlation_id=f"CORR-{app.application_id}"
        ))
        if app.screening_decision:
            audit_counter += 1
            db.add(AuditEvent(
                event_id=f"AUD-EVAL-{audit_counter:06d}",
                event_type="SCREENING_EVALUATED",
                entity_type="Application",
                entity_id=app.application_id,
                actor="Screening Engine v1.0",
                timestamp=app.application_date + datetime.timedelta(days=1),
                previous_state="Applied",
                new_state=app.stage,
                reason=f"Score: {app.screening_score} | Decision: {app.screening_decision}",
                correlation_id=f"CORR-{app.application_id}"
            ))

    # Offer audit events
    for off in offers:
        audit_counter += 1
        db.add(AuditEvent(
            event_id=f"AUD-OFF-{audit_counter:06d}",
            event_type="OFFER_CREATED",
            entity_type="Offer",
            entity_id=off.offer_id,
            actor=off.approver or "Talent Acquisition",
            timestamp=off.created_at,
            previous_state=None,
            new_state="Pending Approval",
            reason=f"Proposed salary: ${off.proposed_salary:,.2f}",
            correlation_id=f"CORR-{off.offer_id}"
        ))
        if off.status in ["Accepted", "Declined", "Approved", "Extended"]:
            audit_counter += 1
            db.add(AuditEvent(
                event_id=f"AUD-OFF-{audit_counter:06d}",
                event_type=f"OFFER_{off.status.upper()}",
                entity_type="Offer",
                entity_id=off.offer_id,
                actor="Candidate" if off.status in ["Accepted", "Declined"] else (off.approver or "Approver"),
                timestamp=off.created_at + datetime.timedelta(days=2),
                previous_state="Pending Approval",
                new_state=off.status,
                reason=f"Offer transition to {off.status}",
                correlation_id=f"CORR-{off.offer_id}"
            ))

    # Anomaly audit events
    for anom in [anom_a, anom_b, anom_c, anom_d, anom_e]:
        audit_counter += 1
        db.add(AuditEvent(
            event_id=f"AUD-ANOM-{audit_counter:06d}",
            event_type="ANOMALY_RECORDED",
            entity_type=anom.entity_type,
            entity_id=anom.entity_id,
            actor="System Sentinel",
            timestamp=anom.detected_at,
            previous_state=None,
            new_state=anom.issue_type,
            reason=anom.description,
            correlation_id=f"CORR-{anom.anomaly_id}"
        ))

    db.commit()

    # 12. Save Ground Truth Files
    os.makedirs(os.path.join(PROJECT_ROOT, "ground_truth"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "generated"), exist_ok=True)

    gt_json_path = os.path.join(PROJECT_ROOT, "ground_truth", "ground_truth.json")
    with open(gt_json_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth_records, f, indent=2)

    gt_csv_path = os.path.join(PROJECT_ROOT, "data", "generated", "ground_truth.csv")
    with open(gt_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ground_truth_records[0].keys()))
        writer.writeheader()
        writer.writerows(ground_truth_records)

    print(f"[+] Successfully generated dataset and exported ground truth to {gt_json_path} and {gt_csv_path}!")
    print(f"[+] Final Database State: {db.query(JobRequisition).count()} Reqs, {db.query(Candidate).count()} Candidates, {db.query(Application).count()} Apps, {db.query(Interview).count()} Interviews, {db.query(Offer).count()} Offers, {db.query(AnomalyRecord).count()} Anomalies.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator for YottaFlex Recruitment System")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed (default: 20261022)")
    parser.add_argument("--scale", type=str, choices=["starter", "full"], default="starter", help="Dataset scale: starter or full")
    args = parser.parse_args()

    generate_synthetic_dataset(seed=args.seed, scale=args.scale)
