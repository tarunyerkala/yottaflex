import os
import sys
import argparse
import json
import csv
import hashlib
import datetime
from sqlalchemy import inspect

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.db.database import SessionLocal
from backend.app.models.models import (
    Department, Skill, JobRequisition, RequisitionSkill, RequisitionApproval,
    Candidate, CandidateSkill, ResumeArtifact, ScreeningRule,
    Application, ScreeningEvaluation, ApplicationStageHistory,
    Interviewer, InterviewerAvailability, Interview, InterviewPanelMember, Feedback,
    Offer, OfferApproval, OfferStatusHistory, AuditEvent, AnomalyRecord
)

TABLE_MODELS = [
    ("departments", Department),
    ("skills", Skill),
    ("job_requisitions", JobRequisition),
    ("requisition_skills", RequisitionSkill),
    ("requisition_approvals", RequisitionApproval),
    ("candidates", Candidate),
    ("candidate_skills", CandidateSkill),
    ("resume_artifacts", ResumeArtifact),
    ("screening_rules", ScreeningRule),
    ("applications", Application),
    ("screening_evaluations", ScreeningEvaluation),
    ("application_stage_history", ApplicationStageHistory),
    ("interviewers", Interviewer),
    ("interviewer_availabilities", InterviewerAvailability),
    ("interviews", Interview),
    ("interview_panel_members", InterviewPanelMember),
    ("feedbacks", Feedback),
    ("offers", Offer),
    ("offer_approvals", OfferApproval),
    ("offer_status_history", OfferStatusHistory),
    ("audit_events", AuditEvent),
    ("anomaly_records", AnomalyRecord)
]


def serialize_value(val):
    if val is None:
        return ""
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    return str(val)


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def export_dataset(export_format: str, output_dir: str = None, db_session=None):
    db = db_session or SessionLocal()
    export_format = export_format.lower()
    base_out = output_dir or os.path.join(PROJECT_ROOT, "data", "exports", export_format)
    os.makedirs(base_out, exist_ok=True)

    manifest_entries = []

    try:
        print(f"[*] Exporting dataset to {export_format.upper()} format in: {base_out}")

        if export_format == "sql":
            sql_file_path = os.path.join(base_out, "seed_data.sql")
            with open(sql_file_path, "w", encoding="utf-8") as sql_file:
                sql_file.write("-- YottaFlex AI Database Seed Export\n")
                sql_file.write(f"-- Exported on {datetime.datetime.utcnow().isoformat()}\n\n")

                for table_name, model in TABLE_MODELS:
                    records = db.query(model).order_by(model.id).all()
                    if not records:
                        continue
                    cols = [c.name for c in model.__table__.columns]
                    col_str = ", ".join(cols)

                    for r in records:
                        vals = []
                        for c in cols:
                            val = getattr(r, c)
                            if val is None:
                                vals.append("NULL")
                            elif isinstance(val, (int, float)):
                                vals.append(str(val))
                            elif isinstance(val, bool):
                                vals.append("1" if val else "0")
                            else:
                                clean_val = str(val).replace("'", "''")
                                vals.append(f"'{clean_val}'")
                        val_str = ", ".join(vals)
                        sql_file.write(f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str});\n")

            checksum = compute_sha256(sql_file_path)
            manifest_entries.append({
                "table_name": "all_tables_sql",
                "format": "sql",
                "file_path": sql_file_path,
                "row_count": sum(db.query(m).count() for _, m in TABLE_MODELS),
                "sha256": checksum
            })
            print(f"  [+] Exported SQL seed script to {sql_file_path}")

        elif export_format == "csv":
            for table_name, model in TABLE_MODELS:
                records = db.query(model).order_by(model.id).all()
                csv_path = os.path.join(base_out, f"{table_name}.csv")
                cols = [c.name for c in model.__table__.columns]

                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(cols)
                    for r in records:
                        writer.writerow([serialize_value(getattr(r, c)) for c in cols])

                checksum = compute_sha256(csv_path)
                manifest_entries.append({
                    "table_name": table_name,
                    "format": "csv",
                    "file_path": csv_path,
                    "row_count": len(records),
                    "sha256": checksum
                })
                print(f"  [+] Exported {table_name}: {len(records)} rows -> {csv_path}")

        elif export_format == "json":
            for table_name, model in TABLE_MODELS:
                records = db.query(model).order_by(model.id).all()
                json_path = os.path.join(base_out, f"{table_name}.json")
                cols = [c.name for c in model.__table__.columns]

                data_list = []
                for r in records:
                    row_dict = {}
                    for c in cols:
                        val = getattr(r, c)
                        if isinstance(val, (datetime.datetime, datetime.date)):
                            row_dict[c] = val.isoformat()
                        else:
                            row_dict[c] = val
                    data_list.append(row_dict)

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data_list, f, indent=2)

                checksum = compute_sha256(json_path)
                manifest_entries.append({
                    "table_name": table_name,
                    "format": "json",
                    "file_path": json_path,
                    "row_count": len(records),
                    "sha256": checksum
                })
                print(f"  [+] Exported {table_name}: {len(records)} records -> {json_path}")

        # Write export manifest
        manifest_dir = os.path.join(PROJECT_ROOT, "data", "manifests")
        os.makedirs(manifest_dir, exist_ok=True)
        manifest_file = os.path.join(manifest_dir, f"export_manifest_{export_format}.json")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump({
                "generator_version": "1.0.0",
                "seed": 20261022,
                "exported_at": datetime.datetime.utcnow().isoformat(),
                "format": export_format,
                "tables": manifest_entries
            }, f, indent=2)

    finally:
        if not db_session:
            db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export YottaFlex Recruitment Dataset")
    parser.add_argument("--format", type=str, choices=["csv", "json", "sql"], required=True, help="Export format")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    export_dataset(args.format, args.output)
