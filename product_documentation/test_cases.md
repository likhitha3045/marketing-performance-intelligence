# Test cases

| ID | Scenario | Expected result |
|---|---|---|
| DATA-01 | Regenerate the sample data | Same row counts and values on each run |
| DATA-02 | Remove a required CSV | Loader raises a clear `FileNotFoundError` naming the file |
| DATA-03 | Add an invalid date or negative spend | Validation rejects the source before loading |
| DATA-04 | Add an unknown campaign/customer reference | Relationship validation fails with the source field |
| SQL-01 | Compare campaign spend and revenue | Each fact is aggregated independently; totals are not multiplied |
| KPI-01 | Set denominator to zero | Rate, CPC, CPA, and ROAS return 0 instead of an exception |
| FILTER-01 | Select a channel and campaign | Dashboard facts are limited to the selected scope |
| FILTER-02 | Select customer region/segment | Customer Insights changes; campaign, funnel, and ROI totals remain on the full selected campaign/date scope |
| FUNNEL-01 | View funnel stages | Stage counts and prior-stage rates are displayed |
| REC-01 | Save a recommendation action | Status and manager note can be retrieved from SQLite |
| EXPORT-01 | Download campaign and channel CSV | Filtered scorecards are valid CSV with headers |
| EXPORT-02 | Download PDF report | A non-empty PDF is produced with KPIs, campaign/channel tables, and caveat |
| DEPLOY-01 | Deploy from GitHub using `requirements.txt` | App installs, seeds SQLite, and opens all eleven pages |
| UPLOAD-01 | Upload all eight valid CSVs | Dashboard switches to uploaded data for the current session |
| UPLOAD-02 | Omit a required CSV or use an invalid reference | Show a validation error and keep the sample selected |
| UPLOAD-03 | Upload valid files | Bundled synthetic CSVs remain unchanged |
| FINDING-01 | Open analyst findings | Each observation includes metric evidence and a next-step validation |
| FORECAST-01 | Select fewer than four monthly data points | Explain why a forecast is unavailable |
| FORECAST-02 | Select at least six monthly data points | Show linear forecast, approximate range, and two-month holdout error |
