# Product roadmap

| Phase | Priority | Deliverables | Exit criteria |
|---|---|---|---|
| 1. Data foundation | Must | Synthetic source data, validation, SQLite schema, relationships | Reproducible load; constraints and data checks pass |
| 2. Analysis | Must | 22 SQL examples and validated KPI formulas | Campaign/channel totals avoid fact-join duplication |
| 3. Dashboard MVP | Must | Eleven modules, filters, charts, report exports | Core journeys work on sample and validated uploaded data |
| 4. Decision support | Must | Evidence-based opportunity cards and action status | Recommendation evidence matches selected metrics |
| 5. Portfolio polish | Must | PRD, personas, stories, roadmap, KPI plan, Power BI handoff | Another analyst can understand and reproduce the product |
| 6. Public demo | Must | GitHub repository and Streamlit Community Cloud app | Public synthetic-data demo is accessible |
| 7. Production readiness | Later | Authentication, managed PostgreSQL, audit trail, secrets, monitoring | Security and persistence reviewed before real data use |
| 8. Forecast quality | Later | Seasonality-aware models and rolling-origin backtests | Baselines outperform simple holdout references on appropriate data |
| 9. Measurement quality | Later | Attribution validation, margin, incrementality experiments | Business ROI is not inferred from ROAS alone |

## Prioritization

The MVP favors reliable definitions, useful comparisons, and actionable exports over live integrations or sophisticated predictive features. Login is deferred; production persistence and identity need a chosen provider. Do not use the local SQLite action store for team-critical decisions.
