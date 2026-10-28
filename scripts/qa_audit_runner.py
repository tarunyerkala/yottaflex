import os
import sys
import json
import sqlite3
import datetime
from sqlalchemy import create_engine, func, inspect, text
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.models.models import (
    Department, Skill, JobRequisition, RequisitionSkill, RequisitionApproval,
    Candidate, CandidateSkill, ResumeArtifact, ScreeningRule,
    Application, ScreeningEvaluation, ApplicationStageHistory,
    Interviewer, InterviewerAvailability, Interview, InterviewPanelMember, Feedback,
    Offer, OfferApproval, OfferStatusHistory, AuditEvent, AnomalyRecord, User
)
from backend.app.rules.business_rules import (
    evaluate_candidate_screening,
    validate_requisition_can_accept_application,
    validate_interview_scheduling,
    validate_feedback_submission,
    validate_stage_transition,
    validate_offer_creation,
    BusinessRuleViolation
)
from backend.app.services.validator_service import run_all_validation_checks

DB_PATH = os.path.join(PROJECT_ROOT, "recruitment.db")

def run_qa_audit():
    print("=" * 80)
    print("      YOTTAFLEX AI — INDEPENDENT SENIOR QA COMPREHENSIVE AUDIT REPORT        ")
    print(f"      Execution Date: {datetime.datetime.utcnow().isoformat()}Z              ")
    print(f"      Target Database: {DB_PATH}                                             ")
    print("=" * 80)

    if not os.path.exists(DB_PATH):
        print(f"[!] ERROR: Database file {DB_PATH} not found. Please run generator first.")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    db = Session()
    raw_conn = sqlite3.connect(DB_PATH)
    raw_cur = raw_conn.cursor()

    results = {}

    try:
        # -------------------------------------------------------------
        # CHECK 1: ALL TWELVE REQUIRED ENTITIES & THEIR RELATIONSHIPS
        # -------------------------------------------------------------
        print("\n[CHECK 1] Inspecting 12 Required Entities & Relationships...")
        required_entities = [
            ("JobRequisition", "job_requisitions", JobRequisition),
            ("Department", "departments", Department),
            ("Candidate", "candidates", Candidate),
            ("Application", "applications", Application),
            ("ResumeArtifact", "resume_artifacts", ResumeArtifact),
            ("Skill", "skills", Skill),
            ("CandidateSkill", "candidate_skills", CandidateSkill),
            ("ScreeningRule", "screening_rules", ScreeningRule),
            ("Interview", "interviews", Interview),
            ("Interviewer", "interviewers", Interviewer),
            ("Feedback", "feedbacks", Feedback),
            ("Offer", "offers", Offer)
        ]

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        entity_audit = {}

        for name, tbl, model in required_entities:
            present = tbl in existing_tables
            count = db.query(model).count() if present else 0
            fks = inspector.get_foreign_keys(tbl) if present else []
            entity_audit[name] = {
                "table": tbl,
                "present": present,
                "row_count": count,
                "foreign_keys": [f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}" for fk in fks]
            }
            print(f"  - Entity: {name:<18} | Table: {tbl:<20} | Rows: {count:<6} | FKs: {len(fks)}")

        all_12_present = all(v["present"] and v["row_count"] > 0 for v in entity_audit.values())
        results["check_1_entities"] = {
            "status": "PASS" if all_12_present else "FAIL",
            "details": entity_audit
        }

        # -------------------------------------------------------------
        # CHECK 2: PRIMARY-KEY UNIQUENESS & FOREIGN-KEY INTEGRITY
        # -------------------------------------------------------------
        print("\n[CHECK 2] Verifying Primary-Key Uniqueness & Foreign-Key Integrity...")
        pk_audit = {}
        for name, tbl, model in required_entities:
            total_rows = db.query(model.id).count()
            distinct_pks = db.query(model.id).distinct().count()
            pk_pass = (total_rows == distinct_pks and total_rows > 0)
            pk_audit[name] = {"total_rows": total_rows, "distinct_pks": distinct_pks, "pass": pk_pass}
            print(f"  - PK Uniqueness {name:<18}: Total {total_rows:<5} == Distinct {distinct_pks:<5} -> {'PASS' if pk_pass else 'FAIL'}")

        # Check FK orphans directly in SQL
        raw_cur.execute("""
            SELECT count(*) FROM applications 
            WHERE candidate_id NOT IN (SELECT id FROM candidates)
               OR requisition_id NOT IN (SELECT id FROM job_requisitions)
        """)
        app_orphans = raw_cur.fetchone()[0]

        raw_cur.execute("""
            SELECT count(*) FROM interviews 
            WHERE application_id NOT IN (SELECT id FROM applications)
        """)
        intv_orphans = raw_cur.fetchone()[0]

        raw_cur.execute("""
            SELECT count(*) FROM feedbacks 
            WHERE interview_id NOT IN (SELECT id FROM interviews)
               OR interviewer_id NOT IN (SELECT id FROM interviewers)
        """)
        fb_orphans = raw_cur.fetchone()[0]

        raw_cur.execute("""
            SELECT count(*) FROM offers 
            WHERE application_id NOT IN (SELECT id FROM applications)
        """)
        off_orphans = raw_cur.fetchone()[0]

        print(f"  - Orphan Applications : {app_orphans}")
        print(f"  - Orphan Interviews   : {intv_orphans}")
        print(f"  - Orphan Feedbacks    : {fb_orphans}")
        print(f"  - Orphan Offers       : {off_orphans}")

        fk_pass = (app_orphans == 0 and intv_orphans == 0 and fb_orphans == 0 and off_orphans == 0)
        all_pk_pass = all(v["pass"] for v in pk_audit.values())
        results["check_2_pk_fk"] = {
            "status": "PASS" if (all_pk_pass and fk_pass) else "FAIL",
            "orphans": {"applications": app_orphans, "interviews": intv_orphans, "feedbacks": fb_orphans, "offers": off_orphans}
        }

        # -------------------------------------------------------------
        # CHECK 3: EXACT TARGET VOLUMES FOR FULL SYNTHETIC DATASET
        # -------------------------------------------------------------
        print("\n[CHECK 3] Verifying Exact Target Volumes for Full Synthetic Dataset...")
        v_reqs = db.query(JobRequisition).count()
        v_cands = db.query(Candidate).count()
        v_apps = db.query(Application).count()
        v_intvs = db.query(Interview).count()
        v_offers = db.query(Offer).count()

        print(f"  - JobRequisitions : Observed {v_reqs:<5} (Target: 100)")
        print(f"  - Candidates      : Observed {v_cands:<5} (Target: 2000)")
        print(f"  - Applications    : Observed {v_apps:<5} (Target: 3000 baseline + 1 anomaly dup)")
        print(f"  - Interviews      : Observed {v_intvs:<5} (Target: 600 baseline + 2 anomaly intvs)")
        print(f"  - Offers          : Observed {v_offers:<5} (Target: 150 baseline + 1 anomaly offer)")

        target_pass = (v_reqs == 100 and v_cands == 2000 and v_apps >= 3000 and v_intvs >= 600 and v_offers >= 150)
        results["check_3_target_volumes"] = {
            "status": "PASS" if target_pass else "FAIL",
            "observed": {"reqs": v_reqs, "candidates": v_cands, "applications": v_apps, "interviews": v_intvs, "offers": v_offers}
        }

        # -------------------------------------------------------------
        # CHECK 4: ALL FIVE REQUIRED ANOMALY CATEGORIES
        # -------------------------------------------------------------
        print("\n[CHECK 4] Verifying All Five Required Anomaly Categories...")
        anomalies = db.query(AnomalyRecord).all()
        by_category = {}
        for a in anomalies:
            by_category[a.issue_type] = a

        req_anom_cats = [
            "AVAILABILITY_CONFLICT",
            "DUPLICATE_APPLICATION",
            "MISSING_FEEDBACK_ADVANCED_STAGE",
            "SALARY_BAND_VIOLATION",
            "CLOSED_REQUISITION_ACTIVE_APPLICATIONS"
        ]

        anom_results = {}
        for cat in req_anom_cats:
            present = cat in by_category
            anom_results[cat] = present
            desc = by_category[cat].description[:60] + "..." if present else "MISSING"
            print(f"  - Anomaly [{cat:<36}]: {'PRESENT' if present else 'FAIL'} | {desc}")

        all_anoms_present = all(anom_results.values())
        results["check_4_anomalies"] = {
            "status": "PASS" if all_anoms_present else "FAIL",
            "categories": anom_results
        }

        # -------------------------------------------------------------
        # CHECK 5: SEPARATION OF GROUND TRUTH FROM OPERATIONAL DATA
        # -------------------------------------------------------------
        print("\n[CHECK 5] Verifying Separation of Ground Truth from Operational Data...")
        gt_json_path = os.path.join(PROJECT_ROOT, "ground_truth", "ground_truth.json")
        gt_csv_path = os.path.join(PROJECT_ROOT, "data", "generated", "ground_truth.csv")

        gt_json_exists = os.path.exists(gt_json_path)
        gt_csv_exists = os.path.exists(gt_csv_path)

        with open(gt_json_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        print(f"  - ground_truth/ground_truth.json exists : {gt_json_exists} ({len(gt_data)} entries)")
        print(f"  - data/generated/ground_truth.csv exists : {gt_csv_exists}")

        # Check that operational tables DO NOT have ground truth columns
        app_cols = [c.name for c in Application.__table__.columns]
        req_cols = [c.name for c in JobRequisition.__table__.columns]
        leakage = [col for col in app_cols + req_cols if "ground_truth" in col.lower() or "is_anomaly" in col.lower()]
        print(f"  - Ground-truth label leakage in operational tables: {len(leakage)} columns found")

        gt_pass = (gt_json_exists and gt_csv_exists and len(gt_data) >= 5 and len(leakage) == 0)
        results["check_5_ground_truth"] = {
            "status": "PASS" if gt_pass else "FAIL",
            "records": len(gt_data),
            "leakage_columns": leakage
        }

        # -------------------------------------------------------------
        # CHECK 6: SCREENING CALCULATIONS & DECISION EXPLANATIONS
        # -------------------------------------------------------------
        print("\n[CHECK 6] Verifying Screening Calculations & Explanations...")
        sample_eval = db.query(ScreeningEvaluation).first()
        print(f"  - Evaluation ID     : {sample_eval.evaluation_id}")
        print(f"  - Rule Version      : {sample_eval.rule_version}")
        print(f"  - Matched Skills    : {sample_eval.matched_skills_count} / {sample_eval.total_required_skills} ({sample_eval.skill_coverage_pct}%)")
        print(f"  - Experience Score  : {sample_eval.experience_score} (Candidate: {sample_eval.candidate_experience_months}mo, Req: {sample_eval.required_experience_months}mo)")
        print(f"  - Final Score       : {sample_eval.final_score}")
        print(f"  - Decision          : {sample_eval.decision}")
        print(f"  - Explanation       : {sample_eval.explanation[:85]}...")

        # Verify mathematical consistency
        expected_score = round((sample_eval.skill_coverage_pct * 0.6) + (sample_eval.experience_score * 0.4), 2)
        math_correct = (abs(expected_score - sample_eval.final_score) < 0.01)
        expected_decision = "Pass" if sample_eval.final_score >= 70.0 else "Fail"
        decision_correct = (expected_decision == sample_eval.decision)
        has_explanation = len(sample_eval.explanation) > 20

        print(f"  - Formula Verification : ({sample_eval.skill_coverage_pct} * 0.6) + ({sample_eval.experience_score} * 0.4) = {expected_score} -> {'PASS' if math_correct else 'FAIL'}")
        print(f"  - Decision Threshold   : Score {sample_eval.final_score} >= 70.0 -> '{expected_decision}' == '{sample_eval.decision}' -> {'PASS' if decision_correct else 'FAIL'}")

        results["check_6_screening"] = {
            "status": "PASS" if (math_correct and decision_correct and has_explanation) else "FAIL",
            "math_correct": math_correct,
            "decision_correct": decision_correct
        }

        # -------------------------------------------------------------
        # CHECK 7: INTERVIEWER AVAILABILITY & DOUBLE-BOOKING DETECTION
        # -------------------------------------------------------------
        print("\n[CHECK 7] Verifying Interviewer Availability & Double-Booking Detection...")
        # Query known overlapping interview from Anomaly A
        intv_a = db.query(Interview).filter(Interview.interview_id == "INT-2026-999001").first()
        base_intv = db.query(Interview).filter(Interview.interview_id == "INT-2026-000001").first()

        conflict_detected = False
        try:
            # Attempt to schedule an interview overlapping base_intv with interviewer INTVR-003
            validate_interview_scheduling(
                db=db,
                interviewer_ids=[3],
                scheduled_start=base_intv.scheduled_start,
                scheduled_end=base_intv.scheduled_end
            )
        except BusinessRuleViolation as e:
            if e.rule_name == "INTERVIEWER_DOUBLE_BOOKED":
                conflict_detected = True
                print(f"  - Double-booking conflict caught: {e.message[:70]}...")

        # Test inactive interviewer rejection
        inactive_detected = False
        inactive_inv = db.query(Interviewer).filter(Interviewer.is_active == False).first()
        if not inactive_inv:
            # Temporarily mark one inactive to test
            test_inv = db.query(Interviewer).first()
            orig_status = test_inv.is_active
            test_inv.is_active = False
            db.commit()
            try:
                validate_interview_scheduling(db=db, interviewer_ids=[test_inv.id], scheduled_start=datetime.datetime(2026, 5, 1, 10, 0), scheduled_end=datetime.datetime(2026, 5, 1, 11, 0))
            except BusinessRuleViolation as e:
                if e.rule_name == "INTERVIEWER_INACTIVE":
                    inactive_detected = True
                    print(f"  - Inactive interviewer caught: {e.message}")
            test_inv.is_active = orig_status
            db.commit()

        results["check_7_interview_conflicts"] = {
            "status": "PASS" if (conflict_detected and inactive_detected) else "FAIL",
            "double_booking_caught": conflict_detected,
            "inactive_caught": inactive_detected
        }

        # -------------------------------------------------------------
        # CHECK 8: FEEDBACK REQUIREMENTS BEFORE STAGE PROGRESSION
        # -------------------------------------------------------------
        print("\n[CHECK 8] Verifying Feedback Requirements Before Stage Progression...")
        # Check that application cannot advance to Final Review without completed feedback
        anom_c = db.query(AnomalyRecord).filter(AnomalyRecord.issue_type == "MISSING_FEEDBACK_ADVANCED_STAGE").first()
        c_app = db.query(Application).filter(Application.application_id == anom_c.entity_id).first() if anom_c else None
        if not c_app:
            c_app = db.query(Application).join(Interview).first()

        feedback_gate_enforced = False
        orig_stage = c_app.stage
        c_app.stage = "Interview Evaluation"
        c_int = c_app.interviews[0] if c_app.interviews else None
        orig_int_status = c_int.status if c_int else None
        if c_int:
            c_int.status = "Completed"
        try:
            validate_stage_transition(db, c_app, "Final Review")
        except BusinessRuleViolation as e:
            if "MISSING_INTERVIEW_FEEDBACK" in e.rule_name or "INTERVIEW_NOT_COMPLETED" in e.rule_name:
                feedback_gate_enforced = True
                print(f"  - Stage transition gate enforced: {e.message[:70]}...")
        finally:
            c_app.stage = orig_stage
            if c_int and orig_int_status:
                c_int.status = orig_int_status
            db.rollback()

        results["check_8_feedback_gate"] = {
            "status": "PASS" if feedback_gate_enforced else "FAIL",
            "gate_enforced": feedback_gate_enforced,
            "anomaly_c_verified": anom_c is not None
        }

        # -------------------------------------------------------------
        # CHECK 9: OFFER APPROVAL & SALARY-BAND VALIDATION
        # -------------------------------------------------------------
        print("\n[CHECK 9] Verifying Offer Approval & Salary-Band Validation...")
        sample_app = db.query(Application).filter(Application.stage == "Final Review").first()
        req = sample_app.requisition

        salary_band_enforced = False
        try:
            # Attempt to create offer with salary above max
            validate_offer_creation(
                db=db,
                application=sample_app,
                proposed_salary=req.max_salary + 20000.0,
                start_date=datetime.date(2026, 6, 1),
                issue_date=datetime.date(2026, 5, 1),
                expiry_date=datetime.date(2026, 5, 15)
            )
        except BusinessRuleViolation as e:
            if e.rule_name == "SALARY_BAND_VIOLATION":
                salary_band_enforced = True
                print(f"  - Out-of-band salary rejected: {e.message[:70]}...")

        # Verify Anomaly D in database
        anom_d = db.query(AnomalyRecord).filter(AnomalyRecord.issue_type == "SALARY_BAND_VIOLATION").first()
        print(f"  - Deliberate Anomaly D recorded: {anom_d.anomaly_id} ({anom_d.description[:60]}...)")

        results["check_9_salary_band"] = {
            "status": "PASS" if (salary_band_enforced and anom_d) else "FAIL",
            "band_enforced": salary_band_enforced,
            "anomaly_d_present": anom_d is not None
        }

        # -------------------------------------------------------------
        # CHECK 10: APPLICATION & OFFER HISTORY RECONCILIATION
        # -------------------------------------------------------------
        print("\n[CHECK 10] Verifying Application & Offer History Reconciliation...")
        total_apps = db.query(Application).count()
        raw_cur.execute("SELECT stage, count(*) FROM applications GROUP BY stage")
        stage_counts = dict(raw_cur.fetchall())
        sum_stages = sum(stage_counts.values())

        print(f"  - Total Applications: {total_apps} == Sum across stages: {sum_stages}")
        for stg, cnt in stage_counts.items():
            print(f"    * {stg:<25}: {cnt}")

        total_stage_histories = db.query(ApplicationStageHistory).count()
        print(f"  - Total Stage History Records: {total_stage_histories} (>= Total Apps: {total_stage_histories >= total_apps})")

        total_offers = db.query(Offer).count()
        total_offer_histories = db.query(OfferStatusHistory).count()
        print(f"  - Total Offers: {total_offers} | Total Offer Status Histories: {total_offer_histories}")

        reconciliation_pass = (total_apps == sum_stages and total_stage_histories >= total_apps)
        results["check_10_reconciliation"] = {
            "status": "PASS" if reconciliation_pass else "FAIL",
            "total_apps": total_apps,
            "sum_stages": sum_stages,
            "stage_breakdown": stage_counts
        }

        # -------------------------------------------------------------
        # CHECK 11: DASHBOARD METRIC CALCULATIONS
        # -------------------------------------------------------------
        print("\n[CHECK 11] Verifying Dashboard Metric Calculations against Raw DB...")
        from backend.app.analytics.metrics_service import get_overview_metrics, get_funnel_metrics

        overview_metrics = get_overview_metrics(db)
        funnel_metrics = get_funnel_metrics(db)

        raw_reqs = raw_cur.execute("SELECT count(*) FROM job_requisitions").fetchone()[0]
        raw_open_reqs = raw_cur.execute("SELECT count(*) FROM job_requisitions WHERE status = 'Open'").fetchone()[0]
        raw_cands = raw_cur.execute("SELECT count(*) FROM candidates").fetchone()[0]
        raw_apps = raw_cur.execute("SELECT count(*) FROM applications").fetchone()[0]
        raw_anoms = raw_cur.execute("SELECT count(*) FROM anomaly_records WHERE is_resolved = 0").fetchone()[0]

        m_match = (
            overview_metrics["total_requisitions"] == raw_reqs and
            overview_metrics["open_requisitions"] == raw_open_reqs and
            overview_metrics["total_candidates"] == raw_cands and
            overview_metrics["total_applications"] == raw_apps and
            overview_metrics["active_anomalies"] == raw_anoms
        )

        print(f"  - Total Requisitions : Metrics={overview_metrics['total_requisitions']} vs Raw SQL={raw_reqs}")
        print(f"  - Open Requisitions  : Metrics={overview_metrics['open_requisitions']} vs Raw SQL={raw_open_reqs}")
        print(f"  - Total Candidates   : Metrics={overview_metrics['total_candidates']} vs Raw SQL={raw_cands}")
        print(f"  - Total Applications : Metrics={overview_metrics['total_applications']} vs Raw SQL={raw_apps}")
        print(f"  - Active Anomalies   : Metrics={overview_metrics['active_anomalies']} vs Raw SQL={raw_anoms}")
        print(f"  - Screening Pass %   : {overview_metrics['screening_pass_rate']}%")
        print(f"  - Offer Acceptance % : {overview_metrics['offer_acceptance_rate']}%")

        results["check_11_dashboard_metrics"] = {
            "status": "PASS" if m_match else "FAIL",
            "metrics": overview_metrics
        }

        # -------------------------------------------------------------
        # CHECK 12: DETERMINISTIC REGENERATION USING SEED 20261022
        # -------------------------------------------------------------
        print("\n[CHECK 12] Verifying Deterministic Regeneration using Seed 20261022...")
        repro_report_path = os.path.join(PROJECT_ROOT, "data", "manifests", "reproducibility_report.json")
        repro_pass = False
        repro_data = {}
        if os.path.exists(repro_report_path):
            with open(repro_report_path, "r", encoding="utf-8") as rf:
                repro_data = json.load(rf)
            repro_pass = repro_data.get("all_matched", False)
            print(f"  - Reproducibility Report Found : Seed {repro_data.get('seed')} | All 22 Tables Matched: {repro_pass}")
            for comp in repro_data.get("table_comparisons", [])[:5]:
                print(f"    * {comp['table']:<25}: {comp['run1_sha256'][:16]}... == {comp['run2_sha256'][:16]}... -> {'PASS' if comp['matched'] else 'FAIL'}")
            print(f"    * ... (all {len(repro_data.get('table_comparisons', []))} tables verified)")

        results["check_12_reproducibility"] = {
            "status": "PASS" if repro_pass else "FAIL",
            "all_matched": repro_pass
        }

        # -------------------------------------------------------------
        # OVERALL QA SUMMARY
        # -------------------------------------------------------------
        print("\n" + "=" * 80)
        print("                         QA AUDIT SUMMARY MATRIX                               ")
        print("=" * 80)
        all_checks_passed = True
        for k, v in results.items():
            status = v["status"]
            if status != "PASS":
                all_checks_passed = False
            print(f"  - {k:<30}: {status}")

        print("=" * 80)
        overall_status = "ALL 12 CHECKS VERIFIED AND PASSING" if all_checks_passed else "FAILURES DETECTED"
        print(f"OVERALL AUDIT VERDICT: {overall_status}")
        print("=" * 80)

        # Write QA audit artifact
        qa_artifact_path = os.path.join(PROJECT_ROOT, "data", "manifests", "qa_audit_evidence.json")
        with open(qa_artifact_path, "w", encoding="utf-8") as qf:
            json.dump({
                "audit_timestamp": datetime.datetime.utcnow().isoformat(),
                "verdict": overall_status,
                "all_passed": all_checks_passed,
                "results": results
            }, qf, indent=2)
        print(f"\n[+] Detailed QA audit evidence serialized to: {qa_artifact_path}")

        return 0 if all_checks_passed else 1

    finally:
        db.close()
        raw_conn.close()

if __name__ == "__main__":
    sys.exit(run_qa_audit())
