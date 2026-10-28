# YottaFlex AI — Recruitment Management and Analytics System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.55-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-25%20Passed-success.svg)]()
[![Seed](https://img.shields.io/badge/Seed-20261022-purple.svg)]()

## 1. Project Overview & Business Problem
Traditional enterprise recruitment pipelines frequently suffer from unexplainable screening rejections, scheduling conflicts, unapproved salary extensions, duplicate candidate records, and broken audit trails. 

**YottaFlex AI** is an end-to-end recruitment management and analytics platform engineered for complete transparency, deterministic scoring, strict business rule enforcement, and reproducible synthetic data generation.

---

## 2. Key Features
- **12 Required Core Entities & 11 Supporting Tables**: Full relational modeling in SQLAlchemy.
- **Deterministic AI Screening**: 100% transparent formula evaluating skill coverage and normalized experience without protected demographic attributes.
- **Interview Scheduling Sentinel**: Live availability verification and double-booking conflict detection.
- **Stage Progression State Machine**: Enforces prerequisite gates (e.g. requires all panel feedback before advancing).
- **Salary Band Verification**: Rejects offers outside approved requisition compensation ranges.
- **5 Deliberate Anomaly Categories & Decoupled Ground Truth**: Identifies and labels availability conflicts, duplicate submissions, missing feedback, salary band breaches, and closed requisitions with active pipelines.
- **Deterministic Reproducibility**: Seed `20261022` verified bit-for-bit across independent generation runs.
- **Unified Executive Dashboard**: Chart.js analytics, requisition management, candidate pipeline, and anomaly center.

---

## 3. Technology Stack
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0
- **Database**: SQLite (default local setup with `StaticPool` for multi-threaded testing)
- **Frontend**: Responsive Single Page Application (HTML5, Bootstrap 5, Chart.js, FontAwesome) served directly from FastAPI
- **Testing**: pytest, FastAPI TestClient (25 automated test scenarios)
- **Data Engineering**: Deterministic pseudo-random generation (Seed `20261022`), CSV/JSON/SQL export tools

---

## 4. Setup & Execution Instructions

### Prerequisites
- Python 3.10 or higher
- Git

### 4.1 Quick Local Setup (Non-Docker)
```powershell
# 1. Clone repository and navigate to folder
cd c:\yottaflex

# 2. Install dependencies
python -m pip install -r backend/requirements.txt

# 3. Generate the synthetic dataset (Seed 20261022)
python scripts/generate_data.py --seed 20261022 --scale full

# 4. Run the data validation suite
python scripts/validate_data.py --input data/generated

# 5. Execute the automated test suite
pytest backend/tests/test_all.py -v

# 6. Verify bit-for-bit reproducibility
python scripts/reproducibility_check.py --seed 20261022 --scale starter

# 7. Start the Web Application & REST API
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Open **http://localhost:8000** in your browser to access the interactive dashboard!
Swagger API documentation is available at **http://localhost:8000/docs**.

### 4.2 Docker Compose Execution
```bash
docker-compose up --build
```

---

## 5. Seeded Dataset Volumes (Seed 20261022)

| Entity / Table | Starter Volume | Full Volume (Achieved) |
| :--- | :---: | :---: |
| **Job Requisitions** | 10 | **100** |
| **Candidates** | 200 | **2,000** |
| **Applications** | 301 | **3,001** |
| **Interviews** | 62 | **602** |
| **Offers** | 16 | **151** |
| **Feedbacks** | 120 | **1,200** |
| **Audit Events** | 655 | **6,555** |
| **Anomalies Injected** | 5 | **5** |

---

## 6. Required Anomalies & Ground Truth
All 5 required anomaly categories are generated and decoupled from operational decision logic:
1. **Anomaly A (`AVAILABILITY_CONFLICT`)**: Interviewer double-booked across concurrent interview slots.
2. **Anomaly B (`DUPLICATE_APPLICATION`)**: Candidate submitted duplicate applications for the same requisition.
3. **Anomaly C (`MISSING_FEEDBACK_ADVANCED_STAGE`)**: Candidate advanced to Final Review without required panel feedback.
4. **Anomaly D (`SALARY_BAND_VIOLATION`)**: Offer issued with salary outside requisition approved band.
5. **Anomaly E (`CLOSED_REQUISITION_ACTIVE_APPLICATIONS`)**: Requisition closed while candidate pipelines remain active.

Ground truth files are exported to:
- `ground_truth/ground_truth.json`
- `data/generated/ground_truth.csv`

---

## 7. Data Export Commands
```powershell
# Export CSV tables
python scripts/export_data.py --format csv

# Export JSON tables
python scripts/export_data.py --format json

# Export SQL seed script
python scripts/export_data.py --format sql
```

---

## 8. Automated Test Suite (25 Tests)
Run:
```powershell
pytest backend/tests/test_all.py -v
```
All 25 tests pass with 100% success rate:
- Requisition approval enforcement
- Unapproved requisition application rejection
- Candidate registration
- Duplicate application detection
- Deterministic screening score calculation
- Exclusion of protected demographic attributes
- Interview conflict and double-booking detection
- Stage progression feedback gates
- Offer salary band validation
- Expired offer acceptance rejection
- Closed requisition with active application anomaly detection
- Ground truth separation verification

---

## 9. Documentation Map
- [Architecture & Design](docs/architecture.md)
- [Database Schema & Relationships](docs/schema.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Business Rules & Formulas](docs/business_rules.md)
- [Assumptions](docs/assumptions.md)
- [Testing Catalog](docs/testing.md)
- [Metrics & Evaluation](docs/metrics.md)
- [Limitations & Ethical Use](docs/limitations.md)
- [AI Usage & Transparency](docs/ai_usage.md)
- [Prompt History](prompt_history/antigravity_prompts.md)
