import os
import sys
import argparse
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.db.database import SessionLocal
from backend.app.services.validator_service import run_all_validation_checks

def main():
    parser = argparse.ArgumentParser(description="Recruitment System Data Validator")
    parser.add_argument("--input", type=str, default="data/generated", help="Data input directory or database")
    parser.add_argument("--output", type=str, default="data/manifests/validation_report.json", help="Path for JSON validation report")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("================================================================================")
        print("                 YOTTAFLEX AI - DATA INTEGRITY VALIDATION RUN                   ")
        print("================================================================================")

        summary = run_all_validation_checks(db)

        # Print Checks Table
        print(f"\n{'ID':<25} | {'CHECK NAME':<35} | {'CATEGORY':<20} | {'STATUS':<8}")
        print("-" * 96)
        for c in summary["checks"]:
            status_display = c["status"]
            print(f"{c['check_id']:<25} | {c['check_name'][:35]:<35} | {c['category'][:20]:<20} | {status_display:<8}")

        print("\n" + "=" * 80)
        print("                               SUMMARY OVERVIEW                                 ")
        print("=" * 80)
        print(f"Total Validation Checks Run : {summary['total_checks']}")
        print(f"Passed / Verified Checks    : {summary['passed_checks']}")
        print(f"Failed Checks               : {summary['failed_checks']}")
        print(f"Structural Integrity        : {summary['structural_integrity']}")
        print(f"Business Integrity          : {summary['business_integrity']}")
        print(f"Date Integrity              : {summary['date_integrity']}")
        print(f"Anomalies Detection Status  : {summary['anomalies_status']}")
        print("=" * 80)

        # Save machine-readable output
        out_dir = os.path.dirname(os.path.join(PROJECT_ROOT, args.output))
        os.makedirs(out_dir, exist_ok=True)
        report_path = os.path.join(PROJECT_ROOT, args.output)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\n[+] Validation report saved to: {report_path}")

        if summary["failed_checks"] > 0:
            print("[!] Validation failed with errors.")
            sys.exit(1)
        else:
            print("[+] All validation checks passed successfully!")
            sys.exit(0)
    finally:
        db.close()

if __name__ == "__main__":
    main()
