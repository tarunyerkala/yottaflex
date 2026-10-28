# Comprehensive Data Dictionary

## 1. Primary & Business Identifiers Overview
| Entity | Internal PK | Business ID Format | Example | Uniqueness Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Department** | `id` (INTEGER) | `department_id` | `DEP-ENG` | Unique per department code |
| **Skill** | `id` (INTEGER) | `skill_id` | `SKILL-001` | Unique per skill name |
| **JobRequisition** | `id` (INTEGER) | `requisition_id` | `REQ-2026-000001` | Zero-padded unique counter |
| **Candidate** | `id` (INTEGER) | `candidate_id` | `CAND-000001` | Zero-padded unique counter |
| **Application** | `id` (INTEGER) | `application_id` | `APP-REQ-2026-000001-CAND-000001` | Deterministic composite naming |
| **Interview** | `id` (INTEGER) | `interview_id` | `INT-2026-000001` | Zero-padded unique counter |
| **Feedback** | `id` (INTEGER) | `feedback_id` | `FB-INT-2026-000001-INTVR-001` | Composite interview + interviewer |
| **Offer** | `id` (INTEGER) | `offer_id` | `OFF-2026-000001` | Zero-padded unique counter |

---

## 2. Field-Level Specification for Core Entities

### 2.1 JobRequisition (`job_requisitions`)
| Field Name | Type | Required | Allowed Values | Source/Derived | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Yes | > 0 | Source | Internal surrogate primary key. |
| `requisition_id` | VARCHAR(50) | Yes | `REQ-YYYY-NNNNNN` | Source | Business immutable unique identifier. |
| `title` | VARCHAR(200) | Yes | Non-empty text | Source | Official job role title. |
| `department_id` | INTEGER | Yes | Existing Department PK | Source | Foreign key linking hiring department. |
| `location` | VARCHAR(100) | Yes | Location string | Source | Geographic or remote work location. |
| `job_description` | TEXT | Yes | Text | Source | Responsibilities and expectations. |
| `employment_type` | VARCHAR(50) | Yes | Full-time, Contract, Part-time | Source | Employment relationship type. |
| `openings` | INTEGER | Yes | >= 1 | Source | Approved headcount quota. |
| `min_salary` | FLOAT | Yes | >= 0 | Source | Bottom of approved compensation band (USD). |
| `max_salary` | FLOAT | Yes | >= `min_salary` | Source | Top of approved compensation band (USD). |
| `currency` | VARCHAR(10) | Yes | USD, EUR, etc. | Source | Currency code for salary band. |
| `min_experience_months`| INTEGER | Yes | >= 0 | Source | Minimum experience required for screening. |
| `requisition_owner` | VARCHAR(100) | Yes | Name / Email | Source | Hiring manager or recruiter in charge. |
| `approver` | VARCHAR(100) | No | Name / Email | Derived | Executive who signed off on requisition. |
| `approval_status` | VARCHAR(50) | Yes | Draft, Approved, Rejected, Pending | Derived | Current governance approval state. |
| `status` | VARCHAR(50) | Yes | Draft, Open, Closed, On Hold, Filled | Derived | Operational requisition status. |
| `opening_date` | DATE | No | Valid Date | Derived | Date requisition became open to applicants. |
| `closing_date` | DATE | No | >= `opening_date` | Derived | Date requisition was closed. |
| `created_at` | DATETIME | Yes | ISO 8601 | Source | Creation timestamp. |
| `updated_at` | DATETIME | Yes | ISO 8601 | Derived | Last modification timestamp. |

### 2.2 Candidate (`candidates`)
| Field Name | Type | Required | Allowed Values | Source/Derived | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Yes | > 0 | Source | Internal surrogate primary key. |
| `candidate_id` | VARCHAR(50) | Yes | `CAND-NNNNNN` | Source | Immutable candidate business ID. |
| `full_name` | VARCHAR(150) | Yes | Synthetic name | Source | Candidate legal name. |
| `email` | VARCHAR(150) | Yes | `*@example.test` | Source | Synthetic contact email (unique). |
| `phone` | VARCHAR(50) | Yes | Synthetic phone | Source | Synthetic contact phone number. |
| `total_experience_months` | INTEGER | Yes | >= 0 | Source | Verified candidate total experience. |
| `current_location` | VARCHAR(100) | Yes | City, State | Source | Candidate current residence. |
| `profile_summary` | TEXT | No | Text | Source | Professional summary. |
| `created_at` | DATETIME | Yes | ISO 8601 | Source | Registration timestamp. |

### 2.3 Application (`applications`)
| Field Name | Type | Required | Allowed Values | Source/Derived | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Yes | > 0 | Source | Internal surrogate primary key. |
| `application_id` | VARCHAR(100)| Yes | Deterministic format | Source | Composite business identifier. |
| `candidate_id` | INTEGER | Yes | Existing Candidate PK | Source | Candidate applying. |
| `requisition_id` | INTEGER | Yes | Existing Requisition PK| Source | Targeted job opening. |
| `application_date`| DATETIME | Yes | ISO 8601 | Source | Date and time submitted. |
| `source` | VARCHAR(50) | Yes | Career Site, Referral, etc.| Source | Applicant acquisition channel. |
| `stage` | VARCHAR(50) | Yes | 12 valid stages | Derived | Current position in hiring state machine. |
| `status` | VARCHAR(50) | Yes | Active, Archived, Closed, Flagged | Derived | Operational state of application. |
| `screening_score`| FLOAT | No | 0.00 – 100.00 | Derived | Computed weighted screening score. |
| `screening_decision`| VARCHAR(20)| No | Pass, Fail, Pending | Derived | Outcome based on rule threshold. |
| `decision_reason` | TEXT | No | Transparent explanation| Derived | Formula breakdown and details. |
| `is_duplicate` | BOOLEAN | Yes | True / False | Derived | Flag set for intentional duplicate submission. |
| `created_at` | DATETIME | Yes | ISO 8601 | Source | Creation timestamp. |
| `updated_at` | DATETIME | Yes | ISO 8601 | Derived | Last modification timestamp. |

### 2.4 Interview (`interviews`)
| Field Name | Type | Required | Allowed Values | Source/Derived | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Yes | > 0 | Source | Internal surrogate primary key. |
| `interview_id` | VARCHAR(50) | Yes | `INT-YYYY-NNNNNN` | Source | Business interview identifier. |
| `application_id` | INTEGER | Yes | Existing Application PK| Source | Associated applicant. |
| `round_number` | INTEGER | Yes | 1, 2, 3, ... | Source | Sequential round number. |
| `interview_type` | VARCHAR(100)| Yes | Technical, Culture Fit, etc.| Source | Format of the evaluation. |
| `scheduled_start`| DATETIME | Yes | Valid datetime | Source | Scheduled interview commencement. |
| `scheduled_end` | DATETIME | Yes | > `scheduled_start` | Source | Scheduled interview conclusion. |
| `time_zone` | VARCHAR(50) | Yes | UTC, EST, etc. | Source | Scheduling timezone. |
| `meeting_mode` | VARCHAR(50) | Yes | Virtual - Video, In-person | Source | Delivery channel. |
| `status` | VARCHAR(50) | Yes | Scheduled, Completed, Cancelled, Rescheduled | Derived | Current operational lifecycle state. |
| `created_at` | DATETIME | Yes | ISO 8601 | Source | Creation timestamp. |
| `updated_at` | DATETIME | Yes | ISO 8601 | Derived | Modification timestamp. |

### 2.5 Feedback (`feedbacks`)
| Field Name | Type | Required | Allowed Values | Source/Derived | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Yes | > 0 | Source | Internal surrogate primary key. |
| `feedback_id` | VARCHAR(100)| Yes | `FB-<int-id>-<inv-id>` | Source | Business feedback identifier. |
| `interview_id` | INTEGER | Yes | Existing Interview PK | Source | Interview being scored. |
| `interviewer_id` | INTEGER | Yes | Existing Interviewer PK | Source | Assigned panel member. |
| `technical_score`| INTEGER | Yes | 1 to 5 | Source | Technical assessment rating. |
| `problem_solving_score` | INTEGER | Yes | 1 to 5 | Source | Analytical problem-solving rating. |
| `communication_score` | INTEGER | Yes | 1 to 5 | Source | Clarity and presentation rating. |
| `role_competency_score`| INTEGER | Yes | 1 to 5 | Source | Domain-specific competency rating. |
| `overall_recommendation`| VARCHAR(50)| Yes | Strongly Recommend, Recommend, Mixed, Do Not Recommend | Source | Final hiring recommendation. |
| `strengths` | TEXT | No | Text | Source | Key candidate advantages noted. |
| `concerns` | TEXT | No | Text | Source | Identified risks or gaps. |
| `comments` | TEXT | No | Text | Source | Detailed interview notes. |
| `submitted_at` | DATETIME | Yes | ISO 8601 | Source | Time feedback was submitted. |
| `status` | VARCHAR(50) | Yes | Submitted, Draft, Revoked | Derived | Lifecycle status. |

### 2.6 Offer (`offers`)
| Field Name | Type | Required | Allowed Values | Source/Derived | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Yes | > 0 | Source | Internal surrogate primary key. |
| `offer_id` | VARCHAR(50) | Yes | `OFF-YYYY-NNNNNN` | Source | Business immutable offer identifier. |
| `application_id` | INTEGER | Yes | Existing Application PK| Source | Associated applicant receiving offer. |
| `proposed_salary`| FLOAT | Yes | >= 0 | Source | Proposed base compensation. |
| `currency` | VARCHAR(10) | Yes | USD | Source | Denomination of proposed salary. |
| `salary_period` | VARCHAR(20) | Yes | Annual, Hourly | Source | Frequency of salary calculation. |
| `proposed_start_date` | DATE | Yes | Valid date | Source | Target employment commencement date. |
| `issue_date` | DATE | Yes | Valid date | Source | Date offer was formalized. |
| `expiry_date` | DATE | Yes | > `issue_date` | Source | Expiration date of the offer proposal. |
| `status` | VARCHAR(50) | Yes | Draft, Pending Approval, Approved, Extended, Accepted, Declined, Expired, Withdrawn | Derived | Lifecycle state. |
| `approval_status`| VARCHAR(50)| Yes | Pending, Approved, Rejected | Derived | Governance approval state. |
| `approver` | VARCHAR(100)| No | Name / Email | Derived | Executive authority approving package. |
| `created_at` | DATETIME | Yes | ISO 8601 | Source | Creation timestamp. |
| `updated_at` | DATETIME | Yes | ISO 8601 | Derived | Modification timestamp. |
