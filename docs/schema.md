# Database Schema and Relationships

## 1. Twelve Core Entities & Additional Tables

### Core Entities
1. **Department**: Organizational cost center and hiring unit.
2. **Skill**: Normalized technical, professional, and domain competencies.
3. **JobRequisition**: Position specifications, approved salary bands, and headcount.
4. **Candidate**: Anonymized, synthetic candidate profiles.
5. **ResumeArtifact**: Metadata for synthetic candidate resumes.
6. **CandidateSkill**: N:M bridge connecting Candidate to Skill with proficiency and experience.
7. **RequisitionSkill**: N:M bridge connecting Requisition to Skill with mandatory flags and weights.
8. **ScreeningRule**: Configurable evaluation criteria (coverage, experience, thresholds).
9. **Application**: Candidate submission linked to a specific requisition.
10. **Interviewer**: Internal team member qualified to assess competencies.
11. **Interview**: Scheduled evaluation rounds.
12. **Offer**: Formal employment proposals with compensation and expiry terms.

### Supporting Governance & Audit Entities
13. **RequisitionApproval**: Executive approvals recorded for position opening.
14. **InterviewPanelMember**: N:M bridge associating interviewers with interview rounds.
15. **InterviewerAvailability**: Weekly time windows and date-specific availability overrides.
16. **Feedback**: Structured evaluations from panel interviewers (scores 1–5).
17. **ScreeningEvaluation**: Transparent mathematical record of applicant screening.
18. **ApplicationStageHistory**: Chronological audit trail of all candidate lifecycle stage changes.
19. **OfferApproval**: Executive sign-offs on proposed compensation packages.
20. **OfferStatusHistory**: Immutable audit of offer transitions (Draft -> Approved -> Extended -> Accepted).
21. **AuditEvent**: System-wide append-only event ledger.
22. **AnomalyRecord**: Identified exceptions, policy violations, and resolution tracking.
23. **User**: System actors and role assignments.

## 2. Cardinality and Foreign Key Constraints
- `departments` (1) -> `job_requisitions` (N) [FK: `job_requisitions.department_id`]
- `job_requisitions` (1) -> `applications` (N) [FK: `applications.requisition_id`]
- `candidates` (1) -> `applications` (N) [FK: `applications.candidate_id`]
- `candidates` (1) -> `resume_artifacts` (N) [FK: `resume_artifacts.candidate_id`]
- `candidates` (N) <-> `skills` (M) via `candidate_skills` [FKs: `candidate_id`, `skill_id`]
- `job_requisitions` (N) <-> `skills` (M) via `requisition_skills` [FKs: `requisition_id`, `skill_id`]
- `applications` (1) -> `interviews` (N) [FK: `interviews.application_id`]
- `interviews` (N) <-> `interviewers` (M) via `interview_panel_members` [FKs: `interview_id`, `interviewer_id`]
- `interviews` (1) -> `feedbacks` (N) [FK: `feedbacks.interview_id`]
- `applications` (1) -> `offers` (N) [FK: `offers.application_id`]
- `job_requisitions` (1) -> `requisition_approvals` (N) [FK: `requisition_approvals.requisition_id`]
- `applications` (1) -> `application_stage_history` (N) [FK: `application_stage_history.application_id`]
- `offers` (1) -> `offer_approvals` (N) [FK: `offer_approvals.offer_id`]
- `offers` (1) -> `offer_status_history` (N) [FK: `offer_status_history.offer_id`]
- `applications` (1) -> `screening_evaluations` (N) [FK: `screening_evaluations.application_id`]
