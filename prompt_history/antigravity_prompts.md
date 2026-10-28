# YottaFlex AI — Antigravity Prompts and Interaction History

## 1. Initial Master Prompt (User Request)
Date: 2026-10-26T18:19:29+05:30

```markdown
# PROJECT: YottaFlex AI — End-to-End Recruitment Management and Analytics System
Act as a senior full-stack engineer, data engineer, database architect, QA engineer, and technical documentation specialist.
Build a complete, executable recruitment management system that implements the business workflow described below.
[Full prompt received from user covering 12 entities, business rules, API, synthetic data generator, 5 anomalies, ground truth, validation framework, reproducibility check, tests, and documentation]
```

## 2. Implementation Scope and Assisted Areas
- **Backend Architecture & Database**: FastAPI, Pydantic, SQLAlchemy with SQLite database.
- **Domain Modeling**: 12 core entities + 10 supporting entities (Audit, Anomaly, StageHistory, Approvals, ScreeningEvaluations).
- **Business Workflow Engine**: Requisition approval gates, structured deterministic screening, interview scheduling with conflict detection, panel feedback validation, stage progression state machine, and salary-band offer verification.
- **Deterministic Synthetic Data Generator**: Fixed seed `20261022`, supporting both starter (10 reqs / 200 cands / 300 apps) and full (100 reqs / 2,000 cands / 3,000 apps / 600 ints / 150 offers) datasets.
- **Labelled Anomaly Dataset & Ground Truth**: 5 distinct exception categories cleanly decoupled from operational decision rules.
- **Validation Framework**: Structural integrity, date consistency, referential integrity, and business rule enforcement.
- **Frontend Application**: React single-page dashboard and workflow manager with charts and end-to-end integration.
- **Automated Testing Suite**: 25+ pytest unit and integration tests covering normal, boundary, and negative scenarios.
