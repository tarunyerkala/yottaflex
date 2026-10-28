# AI Usage and Transparency Disclosure

## 1. Role of AI in Development
The Antigravity AI coding assistant was used to accelerate full-stack scaffolding, schema definition, data generator design, and automated test authoring.

## 2. Assisted Areas
- **Backend Architecture & Models**: Scaffolding of 12 core entities and 11 supporting tables in SQLAlchemy.
- **Deterministic Data Generator**: Designing the pseudo-random generation pipeline with seed `20261022`.
- **Validation Framework**: Formulating the 24 structural, business, date, and reconciliation checks.
- **Frontend SPA**: Creating the unified dashboard with Chart.js visualization.
- **Automated Tests**: Implementing the 25 pytest test cases.

## 3. Manual Review & Verification Steps
- Independently verified each of the 25 unit and integration tests.
- Independently verified the mathematical formula for candidate screening.
- Verified that ground truth files are completely decoupled from operational detection logic.
- Executed bit-for-bit SHA-256 reproducibility check comparing independent runs.
- Tested the browser frontend against live API endpoints.
