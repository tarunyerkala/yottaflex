# YottaFlex AI Architecture Overview

## 1. System Vision & Objectives
YottaFlex AI is an enterprise recruitment management, evaluation, and analytics platform designed to enforce rigorous hiring governance, transparent and deterministic candidate screening, conflict-free interview scheduling, salary-band offer compliance, and end-to-end auditability.

## 2. High-Level Architectural Diagram
```
                     +---------------------------------------+
                     |    Web Client / Operational Dashboard |
                     |   (HTML5, Chart.js, Bootstrap 5, SPA) |
                     +-------------------+-------------------+
                                         | REST / JSON
                                         v
                     +---------------------------------------+
                     |         FastAPI Gateway & Routers     |
                     |  - Requisitions Router                |
                     |  - Candidates & Applications Router   |
                     |  - Interviews & Panel Feedback Router |
                     |  - Offers & Compensation Router       |
                     |  - Anomaly & Exception Router         |
                     |  - Analytics & Reconciliation Router  |
                     |  - Validation Engine Router           |
                     +-------------------+-------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |             Services Layer            |
                     |  - Screening Engine (Rule-based)      |
                     |  - Scheduling Conflict Sentinel       |
                     |  - Stage Progression State Machine    |
                     |  - Salary Band Verification Service   |
                     |  - Append-Only Audit Logger           |
                     |  - Independent Anomaly Detector       |
                     +-------------------+-------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |       SQLAlchemy ORM & Database       |
                     |       (SQLite with StaticPool)        |
                     +---------------------------------------+
                                         |
                         +---------------+---------------+
                         |                               |
                         v                               v
             +-----------------------+       +-----------------------+
             | Ground Truth Registry |       | Synthetic Generator   |
             | (Decoupled Labels)    |       | Seed: 20261022        |
             +-----------------------+       +-----------------------+
```

## 3. Layered Design Principles
1. **Separation of Concerns**:
   - Presentation (Dashboard UI) communicates exclusively over REST endpoints.
   - API layer handles routing, query validation, and schema marshalling.
   - Domain Services encapsulate business logic and state machine transitions.
   - Models define relational integrity, foreign keys, and indexes.
2. **Ground Truth Decoupling**:
   - Operational detection engines NEVER read ground-truth files to decide validity.
   - Ground truth files (`ground_truth.json`, `ground_truth.csv`) are purely analytical validation benchmarks.
3. **Deterministic Reproducibility**:
   - Generator utilizes seed `20261022` to generate identical datasets bit-for-bit across independent machines.
   - Checksums (SHA-256) verify serialization consistency.
