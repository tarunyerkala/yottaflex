# Automated Testing & Verification Documentation

## 1. Overview
The automated test suite verifies all normal, edge, negative, and anomaly-detection scenarios across the entire recruitment workflow. Tests run in an isolated in-memory test database using `pytest` and `fastapi.testclient.TestClient`.

## 2. Test Matrix (25 Automated Scenarios)
| # | Test Name | Target Functionality | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **01** | `test_01_approved_requisition_creation` | Requisition creation & approval | State changes from Draft to Open |
| **02** | `test_02_rejection_unapproved_requisition_application` | Application to draft req | Rejection with HTTP 400 |
| **03** | `test_03_candidate_creation` | Candidate registration | 201 Created with valid ID |
| **04** | `test_04_valid_application_submission` | Normal application submission | Stage initialized to 'Applied' |
| **05** | `test_05_duplicate_application_detection` | Same candidate & req submission | HTTP 409 Conflict rejection |
| **06** | `test_06_screening_score_calculation` | Weighted screening calculation | Accurate composite math (70.0%) |
| **07** | `test_07_screening_decision_explanation` | Explainable screening decision | Details matched/missing skills |
| **08** | `test_08_exclusion_of_protected_attributes` | Bias prevention | Zero demographic columns |
| **09** | `test_09_valid_interview_scheduling` | Normal interview creation | Scheduled with panel members |
| **10** | `test_10_interviewer_availability_conflict` | Inactive interviewer scheduling | Rejection with HTTP 400 |
| **11** | `test_11_double_booked_interviewer` | Overlapping interview slots | Rejection with HTTP 409 Conflict |
| **12** | `test_12_valid_feedback_submission` | Panel feedback capture | Ratings saved; interview updated |
| **13** | `test_13_invalid_feedback_score` | Out of range score (6/5) | Rejection with HTTP 400/422 |
| **14** | `test_14_rejection_stage_transition_missing_feedback` | Advance stage with 0 feedback | Rejection with HTTP 400 |
| **15** | `test_15_deliberate_inconsistent_stage_history` | Direct jump Applied -> Hired | State machine rejection |
| **16** | `test_16_offer_creation_after_eligibility` | Offer for eligible candidate | Status initialized to Pending Approval |
| **17** | `test_17_rejection_offer_outside_salary_band` | Offer exceeding requisition max | Rejection with HTTP 400 |
| **18** | `test_18_rejection_offer_response_without_approval` | Extending unapproved offer | State machine rejection |
| **19** | `test_19_offer_acceptance` | Candidate accepts valid offer | Status 'Accepted', App 'Hired' |
| **20** | `test_20_rejection_acceptance_expired_offer` | Candidate accepts expired offer | Rejection with HTTP 400 |
| **21** | `test_21_closed_requisition_active_applications` | Anomaly E detection | Scanner detects closed req anomaly |
| **22** | `test_22_invalid_foreign_key_rejection` | Application with invalid candidate | Rejection with HTTP 404 |
| **23** | `test_23_dashboard_metric_reconciliation` | Overview metrics vs raw DB count | 100% reconciliation match |
| **24** | `test_24_ground_truth_separation` | Ground truth file isolation | No cheat columns in core tables |
| **25** | `test_25_deterministic_data_generation` | Reproducibility verification script | Deterministic script exists |

## 3. Execution Commands
```powershell
# Run the complete test suite
pytest backend/tests/test_all.py -v

# Run the comprehensive data integrity validator
python scripts/validate_data.py --input data/generated

# Run bit-for-bit reproducibility check
python scripts/reproducibility_check.py --seed 20261022 --scale starter
```
