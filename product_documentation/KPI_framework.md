# Product and business KPI framework

Keep product-success metrics separate from marketing-performance metrics.

| KPI | Type | Definition | Measurement approach | Cadence |
|---|---|---|---|---|
| Dashboard adoption | Product | Weekly active authorized users ÷ eligible users | Privacy-aware authenticated page-view events in production | Weekly |
| Report generation | Product | Completed report downloads per active user | Record successful CSV/PDF download events | Weekly |
| Time to identify an issue | Product | Median elapsed time from analysis task start to correct issue identification | Moderated usability study with a fixed task and baseline | Per release |
| Recommendation adoption | Product | Recommendations marked Completed ÷ recommendations reviewed | Persist status transitions with user and timestamp in production | Monthly |
| User satisfaction | Product | Average post-task rating on a consistent 1–5 question | Optional in-product survey, report response count and bias | Monthly |
| ROAS | Marketing | Attributed revenue ÷ recorded marketing spend | Conversions and spend facts at a consistent campaign/date selection | Weekly |
| CPA | Marketing | Recorded marketing spend ÷ conversions | Same period and attribution scope for both facts | Weekly |
| Conversion rate | Marketing | Conversions ÷ clicks | Conversion/click definition and deduplication rules documented | Weekly |

## Measurement cautions

- This demo has no login or multi-user telemetry; its local database is not a suitable source for real usage KPIs.
- A report button click can be tracked only after wiring a durable event store and a privacy notice.
- Recommendation completion is a status proxy for adoption, not proof that the action occurred or caused a result.
- ROAS does not equal profit. Add gross margin, cost of goods, attribution quality, and incrementality before making financial claims.
