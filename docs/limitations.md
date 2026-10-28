# Known Limitations & Responsible AI Guidelines

## 1. System Limitations
1. **Decision Support Nature**: Automated screening algorithms provide decision support rather than autonomous hiring authority. Final employment decisions must involve verified human evaluation.
2. **Synthetic Data Boundaries**: Contact details (e.g. `@example.test` emails, `+1-555-` phones) and resume metadata are synthetically simulated.
3. **Calendar Integrations**: Interview scheduling checks internal database availability windows; external Google Calendar / Microsoft Outlook integrations are not bundled in the default local deployment.
4. **Single Currency**: Compensation bands are currently denominated in USD. Multi-currency conversions are not supported in the baseline setup.

## 2. Responsible AI & Fair Hiring Controls
- Strict exclusion of protected characteristics (race, gender, age, disability, photo, religion).
- Deterministic, auditable formulas rather than black-box opaque models.
- Complete explainability logged in `ScreeningEvaluation` for every evaluated applicant.
