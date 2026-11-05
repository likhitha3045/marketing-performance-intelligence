# Wireframe notes

## Shared layout

```text
┌─────────────────────┬───────────────────────────────────────────────┐
│ Product + navigation│ Page title + brief business question         │
│ CSV upload          ├───────────────────────────────────────────────┤
│ Date range          ├───────────────────────────────────────────────┤
│ Channel             │ KPI cards (selected period and filters)       │
│ Campaign            ├──────────────────────┬────────────────────────┤
│ Customer segment    │ Primary trend/chart  │ Comparison / insight   │
│ Customer region     ├──────────────────────┴────────────────────────┤
│                     │ Detail table, caveat, or next action          │
└─────────────────────┴───────────────────────────────────────────────┘
```

## Module variations

- **Executive Overview:** KPI strip, monthly revenue/spend, channel revenue, top campaigns, quick read.
- **Data Analyst Findings:** evidence cards with source metric, suggested validation, and export.
- **Campaign / Channel:** scorecard table beside spend-vs-revenue comparison.
- **Customer Insights:** customer/repeat/value cards and segment/region breakdowns.
- **Conversion Funnel:** ordered stages beside stage conversion and drop-off percentages.
- **Revenue & ROI:** marketing return and CPA with explicit non-profit caveat.
- **Forecast & Trends:** metric/horizon controls, historical trend, approximate band, and holdout error.
- **Growth Opportunities:** evidence cards beside spend/ROAS quadrant.
- **Recommendations:** action evidence and priority beside editable status/manager note.
- **Reports & Export:** active filter summary, CSV/PDF downloads, preview table.

## Interaction principles

Global filters and the eight-file CSV uploader stay visible in the sidebar. Customer segment/region filters affect Customer Insights, not portfolio spend. Findings show evidence and a validation step. Forecasts are visibly labeled as a simple baseline. Avoid implying that an observational correlation proves causal lift.
