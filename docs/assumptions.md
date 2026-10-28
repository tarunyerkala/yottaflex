# Architectural Assumptions & Design Decisions

## 1. Environment & Runtime Assumptions
1. **Local Operation**: The platform is engineered to run locally in a self-contained runtime environment without requiring paid external cloud services, external message queues, or third-party paid APIs.
2. **Database Engine**: SQLite is utilized as the default local relational database for seamless out-of-the-box local execution. For multi-connection testing, SQLAlchemy `StaticPool` is configured to ensure consistent thread-safe execution across transactions.
3. **Frontend Packaging**: The frontend is built as a responsive Single Page Application (SPA) served directly from the FastAPI static mounts on root (`/`), eliminating CORS or separate proxy requirements during local assessment demos.

## 2. Business Logic Assumptions
1. **Application Stages**: 12 standardized stages are strictly enforced across models, APIs, and the UI.
2. **Deterministic IDs**: Primary entities utilize zero-padded counters with clear prefixes (`REQ-2026-XXXXXX`, `CAND-XXXXXX`, `INT-2026-XXXXXX`, `OFF-2026-XXXXXX`) to ensure instant human readability while relational integrity is maintained by surrogate integer primary keys.
3. **Protected Characteristics**: No demographic attributes (age, race, gender, marital status, religion, disability, photo) are stored on candidate models or included in screening features to prevent proxy discrimination and adhere to fair hiring principles.
4. **Deliberate Anomalies Decoupling**: Ground-truth records for the 5 injected anomaly categories are isolated from operational database tables, ensuring the anomaly detector operates independently on raw system records rather than reading cheat labels.
