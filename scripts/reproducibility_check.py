import os
import sys
import argparse
import hashlib
import json
import tempfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.generate_data import generate_synthetic_dataset
from scripts.export_data import export_dataset, compute_sha256, TABLE_MODELS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.database import Base


def run_reproducibility_verification(seed: int = 20261022, scale: str = "starter"):
    print("================================================================================")
    print(f"       YOTTAFLEX REPRODUCIBILITY CHECK - SEED: {seed} - SCALE: {scale.upper()}   ")
    print("================================================================================")

    temp_dir_1 = tempfile.mkdtemp(prefix="yotta_repro_run1_")
    temp_dir_2 = tempfile.mkdtemp(prefix="yotta_repro_run2_")

    try:
        db_path_1 = os.path.join(temp_dir_1, "test1.db")
        db_path_2 = os.path.join(temp_dir_2, "test2.db")

        # RUN 1
        print("\n[*] Executing Generation Run 1...")
        engine_1 = create_engine(f"sqlite:///{db_path_1}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine_1)
        session_1 = sessionmaker(bind=engine_1)()
        generate_synthetic_dataset(seed=seed, scale=scale, db_session=session_1)
        export_dir_1 = os.path.join(temp_dir_1, "csv")
        export_dataset("csv", output_dir=export_dir_1, db_session=session_1)
        session_1.close()

        # RUN 2
        print("\n[*] Executing Generation Run 2 (Clean independent database & environment)...")
        engine_2 = create_engine(f"sqlite:///{db_path_2}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine_2)
        session_2 = sessionmaker(bind=engine_2)()
        generate_synthetic_dataset(seed=seed, scale=scale, db_session=session_2)
        export_dir_2 = os.path.join(temp_dir_2, "csv")
        export_dataset("csv", output_dir=export_dir_2, db_session=session_2)
        session_2.close()

        # COMPARISON
        print("\n" + "=" * 80)
        print(f"{'TABLE NAME':<30} | {'RUN 1 SHA-256':<18} | {'RUN 2 SHA-256':<18} | {'MATCH':<6}")
        print("-" * 80)

        all_matched = True
        comparison_results = []

        for table_name, _ in TABLE_MODELS:
            file_1 = os.path.join(export_dir_1, f"{table_name}.csv")
            file_2 = os.path.join(export_dir_2, f"{table_name}.csv")

            if os.path.exists(file_1) and os.path.exists(file_2):
                hash_1 = compute_sha256(file_1)
                hash_2 = compute_sha256(file_2)
                matched = (hash_1 == hash_2)
                if not matched:
                    all_matched = False
                match_str = "PASS" if matched else "FAIL"
                print(f"{table_name:<30} | {hash_1[:16]}... | {hash_2[:16]}... | {match_str:<6}")
                comparison_results.append({
                    "table": table_name,
                    "run1_sha256": hash_1,
                    "run2_sha256": hash_2,
                    "matched": matched
                })

        print("=" * 80)
        report_file = os.path.join(PROJECT_ROOT, "data", "manifests", "reproducibility_report.json")
        with open(report_file, "w", encoding="utf-8") as rf:
            json.dump({
                "seed": seed,
                "scale": scale,
                "verified_at": os.popen("powershell -Command Get-Date").read().strip(),
                "all_matched": all_matched,
                "table_comparisons": comparison_results
            }, rf, indent=2)

        if all_matched:
            print("\n[+] REPRODUCIBILITY VERIFICATION: 100% BIT-FOR-BIT IDENTICAL!")
            print(f"[+] Detailed report exported to {report_file}")
            return 0
        else:
            print("\n[!] REPRODUCIBILITY VERIFICATION: MISMATCH DETECTED!")
            return 1

    finally:
        shutil.rmtree(temp_dir_1, ignore_errors=True)
        shutil.rmtree(temp_dir_2, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Reproducibility Verification")
    parser.add_argument("--seed", type=int, default=20261022, help="Seed value (default: 20261022)")
    parser.add_argument("--scale", type=str, default="starter", choices=["starter", "full"], help="Dataset scale")
    args = parser.parse_args()

    sys.exit(run_reproducibility_verification(seed=args.seed, scale=args.scale))
