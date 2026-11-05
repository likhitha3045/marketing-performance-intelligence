# User stories and acceptance criteria

## Campaign comparison

**As a marketing manager,** I want to compare campaign spend, conversions, revenue, CPA, and ROAS so that I can prioritize optimization.

- Campaigns are filterable by date, channel, and campaign.
- Zero-conversion campaigns do not produce divide-by-zero errors.
- Spend and conversion totals remain correct when facts are combined.

## Channel allocation

**As a marketing manager,** I want to see channel-level spend and return so that I can decide which budget changes to test.

- Channel scorecards show spend, attributed revenue, conversions, and ROAS.
- The dashboard describes high ROAS as observational evidence, not proof of incremental lift.

## Customer analysis

**As a marketing analyst,** I want to compare acquired customers by region and segment so that I can investigate differences in observed value.

- Region and segment filters affect customer/conversion metrics.
- The dashboard states when spend metrics are not filtered by customer attributes.

## Funnel diagnosis

**As a marketing analyst,** I want to inspect impressions, clicks, leads, and conversions so that I can locate large stage drop-offs.

- Stage volume and conversion/drop-off from the prior stage are visible.
- Funnel counts are labeled as activity aggregates and not implied to be unique people.

## Action tracking

**As a manager,** I want to update a recommendation status and record a decision so that analysis leads to follow-through.

- Each recommendation has a problem, evidence, suggested action, benefit, and priority.
- Status accepts Pending, In Progress, or Completed; a manager note can be saved.

## Reporting

**As an analyst,** I want to export filtered results so that I can share a consistent snapshot.

- Campaign and channel CSVs and a PDF summary respect active filters.
- Exports identify the reporting period and note synthetic-data / ROAS limitations.

## Use a supplied dataset

**As a marketing analyst,** I want to upload a compatible dataset so that I can explore my own permitted data in the dashboard.

- The user uploads all eight named CSV files from the documented schema.
- Missing files, invalid numbers/dates, duplicate keys, or broken references show a clear validation error.
- Valid uploads affect the current session and do not overwrite the bundled sample files.
- Users are warned not to upload confidential data to an unauthenticated public deployment.

## Explore a trend baseline

**As a data analyst,** I want to see a short-horizon revenue or spend trend with a held-out error summary so that I can compare a simple baseline with historical behavior.

- At least four complete months are required.
- A two-month holdout MAE/MAPE is shown when history is sufficient.
- The page explains that the simple linear trend is not seasonality-aware and is not an automatic budget recommendation.

## Read portfolio findings

**As a data analyst,** I want observations to show both the metric evidence and a suggested validation step so that stakeholders can challenge the analysis.

- Findings are calculated from the selected campaign/channel/funnel facts.
- Descriptive comparisons are not presented as causal impact.
