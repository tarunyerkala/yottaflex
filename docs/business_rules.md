# Recruitment Lifecycle Business Rules & Policies

## 1. Requisition Governance
1. **Approval Gate**: Applications cannot be accepted unless `approval_status == 'Approved'`.
2. **Open Status Gate**: Requisitions must be in `status == 'Open'` to accept submissions. Closed, Draft, or On-Hold requisitions reject new applications with HTTP 400.
3. **Closing Disposition Policy**: Closing a requisition with unresolved active candidate applications constitutes a governance anomaly (Anomaly E).

## 2. Structured Screening Evaluation Formula
The automated screening model calculates candidate match deterministically based strictly on job-related criteria. Demographic and protected attributes are strictly excluded from all models and data structures.

### Mathematical Formulation
$$\text{SkillCoveragePct} = \begin{cases} 100.0 & \text{if } \text{TotalRequiredSkills} = 0 \\ \frac{\text{MatchedSkills}}{\text{TotalRequiredSkills}} \times 100.0 & \text{otherwise} \end{cases}$$

$$\text{ExperienceScore} = \begin{cases} 100.0 & \text{if } \text{ReqMinMonths} \le 0 \\ \min\left(100.0, \frac{\text{CandidateMonths}}{\text{ReqMinMonths}} \times 100.0\right) & \text{otherwise} \end{cases}$$

$$\text{FinalScore} = (\text{SkillCoveragePct} \times W_{\text{skill}}) + (\text{ExperienceScore} \times W_{\text{exp}})$$
Where $W_{\text{skill}} = 0.6$ and $W_{\text{exp}} = 0.4$.

- If $\text{FinalScore} \ge \text{PassThreshold}$ ($70.0$), the candidate receives decision `"Pass"` and transitions to `"Screening Passed"`.
- Otherwise, the candidate receives `"Fail"` and transitions to `"Screening Rejected"`.
- All component scores, weights, matched skills, missing skills, and explanations are stored permanently in `ScreeningEvaluation`.

## 3. Interview Scheduling & Conflict Sentinel
1. **Time Ordering**: `scheduled_start < scheduled_end`.
2. **Interviewer Liveness**: Interviewers must be flagged `is_active == True`.
3. **Availability Window**: If weekly availability windows are configured, the scheduled window must fall within the interviewer's configured active hours.
4. **Double-Booking Detection**: An interviewer cannot be scheduled for an interview whose time overlaps with any other non-cancelled interview ($Start_A < End_B \land End_A > Start_B$). Double-booking attempts are rejected with HTTP 409 Conflict.

## 4. Structured Interview Feedback Rules
1. **Authorized Raters**: Only assigned panel members (`InterviewPanelMember`) can submit feedback for an interview.
2. **Score Range**: Technical, Problem-Solving, Communication, and Role-Competency scores must be integers strictly within $[1, 5]$.
3. **Allowed Recommendations**: `Strongly Recommend`, `Recommend`, `Mixed`, `Do Not Recommend`.

## 5. Stage Progression State Machine
Permitted transitions:
- `Applied` $\to$ `Screening`, `Rejected`, `Withdrawn`
- `Screening` $\to$ `Screening Passed`, `Screening Rejected`, `Rejected`, `Withdrawn`
- `Screening Passed` $\to$ `Interview`, `Rejected`, `Withdrawn`
- `Screening Rejected` $\to$ `Withdrawn`
- `Interview` $\to$ `Interview Evaluation`, `Rejected`, `Withdrawn`
- `Interview Evaluation` $\to$ `Final Review`, `Interview`, `Rejected`, `Withdrawn`
- `Final Review` $\to$ `Offer Pending Approval`, `Rejected`, `Withdrawn`
- `Offer Pending Approval` $\to$ `Offer Extended`, `Rejected`, `Withdrawn`
- `Offer Extended` $\to$ `Hired`, `Rejected`, `Withdrawn`

### Transition Gates
- Advancing from `Interview Evaluation` to `Final Review` requires that **ALL** assigned interview panel members have submitted completed feedback. Advancing with missing feedback is rejected (HTTP 400).
- Advancing from `Offer Pending Approval` to `Offer Extended` requires an approved `Offer` record (`approval_status == 'Approved'`).
- Advancing to `Hired` requires an accepted `Offer` (`status == 'Accepted'`).

## 6. Offer Salary Band & Lifecycle Validation
1. **Salary Band Boundary**: Proposed salary must satisfy:
   $$\text{min\_salary} \le \text{proposed\_salary} \le \text{max\_salary}$$
   Offers outside this band are rejected with HTTP 400/422.
2. **Executive Approval Gate**: An offer cannot be extended to a candidate without recorded sign-off from an authorized approver.
3. **Offer Expiry Policy**: If $\text{today} > \text{expiry\_date}$, candidate acceptance is rejected. Expired offers cannot be accepted without an authorized extension.
