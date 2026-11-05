# Product requirements document

## Product

Marketing Performance & Growth Intelligence

## Objective

Help marketing teams understand spend, acquisition, and attributed revenue, identify measurable opportunities, and record follow-up actions in one lightweight workspace.

## MVP users

Marketing managers, marketing analysts, and business/product leaders.

## Functional requirements

1. Provide eleven dashboard modules, including analyst findings and exploratory forecasting.
2. Filter by date, campaign, channel, region, and customer segment.
3. Show KPI definitions and safely handle zero denominators.
4. Compare campaigns and channels using spend, revenue, conversions, CTR, CPC, CPA, and ROAS.
5. Generate recommendations from observed campaign/channel metrics and show supporting evidence.
6. Save a recommendation status and a manager decision note.
7. Export filtered campaign/channel reports as CSV and a summary as PDF.
8. Validate source CSV columns, dates, numeric fields, duplicate keys, and foreign-key references before database loading.
9. Accept a complete, schema-compatible set of eight CSV uploads and analyze it for the current session without overwriting bundled sample data.
10. Forecast monthly spend or attributed revenue with a simple baseline only when sufficient history exists, and show a holdout error summary and model limitations.

## Non-functional requirements

- Reproducible synthetic data and transparent metric definitions.
- Local startup with a documented Python environment.
- Relational constraints and indexes on common join/filter fields.
- No secrets or real personal data in the demonstration.
- Clear limitations for persistence, attribution, and profitability.

## Out of scope

- Live ad-platform integrations, seasonal forecasting, causal attribution, margin-aware profit, access control, and production-grade multi-tenant persistence.
- Login/authentication is deferred until an identity provider and deployment requirements are selected.
- An automatically generated Power BI `.pbix`; users create/save it in Power BI Desktop from the included source data and DAX.

## Acceptance criteria

- An unseeded local app creates and loads the SQLite database from validated CSVs.
- All eleven modules render for the included deterministic sample dataset.
- Filtering changes the relevant metrics; customer filters do not silently change ad-delivery facts.
- Fact tables are aggregated independently before campaign/channel metrics are joined.
- Recommendation evidence is traceable to selected metrics and statuses can be saved.
- CSV and PDF downloads are generated successfully.
- Invalid uploads are rejected with a visible error; accepted uploads provide session-scoped metrics without changing bundled sample CSVs.
- Forecasting requires at least four months and describes its limitations.
- Unit tests pass and deployment instructions are sufficient to launch the app from a GitHub repository.
