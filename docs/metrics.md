# Measurable Evaluation & Operational Metrics

## 1. Funnel & Operational Metrics
| Metric Name | Numerator | Denominator | Definition & Filter |
| :--- | :--- | :--- | :--- |
| **Screening Pass Rate** | Count of applications with `screening_decision == 'Pass'` | Count of evaluated applications | Percentage of screened candidates meeting threshold ($70.0$). |
| **Interview Completion Rate** | Count of interviews with `status == 'Completed'` | Total interviews scheduled | Ratio of conducted evaluations to scheduled appointments. |
| **Offer Acceptance Rate** | Count of offers with `status == 'Accepted'` | Total offers issued | Percentage of formalized job offers accepted by candidates. |
| **Duplicate Submission Rate** | Count of applications where `is_duplicate == True` | Total application submissions | Frequency of redundant candidate submissions. |
| **Salary Band Violation Count** | Count of offers where `salary < min_salary` or `salary > max_salary` | Total offers | Integrity metric checking adherence to approved budget bands. |

## 2. Ground-Truth Anomaly Evaluation
| Anomaly Category | Total Ground Truth Injected | Independently Detected | True Positives | False Positives | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Category A: Availability Conflict** | 1 | 1 | 1 | 0 | 100% | 100% | 1.00 |
| **Category B: Duplicate Application** | 1 | 1 | 1 | 0 | 100% | 100% | 1.00 |
| **Category C: Incomplete Feedback** | 1 | 1 | 1 | 0 | 100% | 100% | 1.00 |
| **Category D: Salary Band Violation** | 1 | 1 | 1 | 0 | 100% | 100% | 1.00 |
| **Category E: Closed Req Active Apps** | 1 | 1 | 1 | 0 | 100% | 100% | 1.00 |
| **Overall Summary** | **5** | **5** | **5** | **0** | **100%**| **100%**| **1.00** |
