# Marketing Performance & Growth Intelligence

A portfolio-ready marketing analytics product for exploring campaign performance, acquisition funnels, customer segments, attributed revenue, and evidence-based growth actions.

> **Dataset notice:** all included records are synthetic, generated with a fixed seed, and intended for demonstration. They are not real customer or campaign data. Currency is Indian rupees (INR).

## What is included

- Eleven interactive dashboard modules, including analyst findings and exploratory forecasting.
- Reproducible Python data generation, cleaning, validation, and SQLite loading pipeline.
- CSV upload for a complete project dataset, validated and analyzed for the current Streamlit session.
- Eight normalized database tables, referential integrity, indexes, and 22 analysis queries.
- Filtered campaign/channel CSV exports and a PDF portfolio report.
- Power BI model setup and DAX measures. The `.pbix` report is authored and saved in Power BI Desktop using the included CSVs; this repository does not contain a generated PBIX binary.
- Product brief, personas, PRD, stories, roadmap, KPI framework, wireframe notes, and test cases.

## Portfolio summary

**Marketing Performance & Growth Intelligence** is a deployed analytics portfolio project that demonstrates an end-to-end workflow for exploring marketing campaign performance. The included dataset is synthetic and designed for demonstration; findings should not be presented as real-company results.

### Resume-ready project points

- Built an interactive Streamlit dashboard with 11 modules to analyze campaign and channel performance, customer segments, conversion funnels, attributed revenue, and growth opportunities.
- Created a reproducible Python data pipeline to generate, validate, and load synthetic marketing data into an indexed SQLite model with eight related tables.
- Wrote 22 SQL analysis queries and implemented CTR, CPC, CPA, conversion rate, and ROAS calculations, aggregating spend and conversion facts independently to prevent duplicated totals.
- Added schema-validated CSV uploads, evidence-backed analyst findings, and an exploratory monthly trend forecast with a two-month holdout error summary.
- Enabled filtered campaign/channel CSV exports, PDF reports, and manager action tracking; prepared Power BI DAX and model setup instructions.
- Documented the product requirements, personas, user stories, roadmap, KPI framework, limitations, and deployment process.

### Skills demonstrated

Python, pandas, NumPy, SQL, SQLite, Streamlit, Plotly, data validation, data visualization, KPI definition, dashboard design, product documentation, and deployment.

### Project limitations to disclose

The sample data is synthetic. The forecast is a simple linear baseline, recommendations are rule-based, ROAS is not net profit or causal lift, and authentication/durable team storage are not included. Do not claim business performance improvements from this demonstration.

## Run locally (Windows PowerShell)

Use Python 3.11 or 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.generate_data
streamlit run app.py
```

The app opens at `http://localhost:8501`. It creates `dataset/marketing.sqlite3` from the checked-in CSV files when first launched. To use your own data instead, upload the required CSV files in the sidebar. The generated database is ignored by Git and can be rebuilt at any time:

```powershell
Remove-Item dataset\marketing.sqlite3
streamlit run app.py
```

The CSV generator is deterministic (`SEED = 20251105`). Run `python -m scripts.generate_data` only when you want to recreate the sample files. The app validates required columns, dates, numeric values, duplicate keys, and foreign-key references before loading the database. Region and segment filters are scoped to Customer Insights; portfolio spend/ROI metrics remain based on a consistent campaign/date selection.

### Upload your own data

In the sidebar, upload all eight CSVs using the exact filenames below. The same required columns and relationships used by the included dataset are validated before the dashboard switches to the upload:

`channels.csv`, `campaigns.csv`, `customers.csv`, `marketing_spend.csv`, `leads.csv`, `conversions.csv`, `products.csv`, `transactions.csv`.

The schemas are documented in [sql/schema.sql](./sql/schema.sql); the included files in `dataset/` are working examples. Uploads are held for the current app session and are not written into the checked-in project. If files are missing or invalid, the app displays the error and keeps the sample selected.

### Forecast limitations

Forecast & Trends requires at least four months and fits a simple linear trend to the selected monthly metric. Its shaded residual range is approximate, and its two-month holdout errors are descriptive, not a guarantee of future accuracy. It does not model seasonality, causal effects, or external events; do not use it as an automatic budget decision.

## Deploy to Streamlit Community Cloud

1. Create an empty GitHub repository. In PowerShell, from this project folder, run the following and replace the remote URL with your repository URL:

   ```powershell
   git init
   git add .
   git commit -m "Add marketing intelligence dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repository-name>.git
   git push -u origin main
   ```

   Keep the synthetic CSVs in the repository so the hosted app can seed its database.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub and select **Create app**.
3. Choose the repository, branch, and `app.py` as the entry point; select **Deploy**.
4. The service installs packages from `requirements.txt`, builds the local SQLite database from `dataset/*.csv`, and starts the dashboard. No API keys or secrets are required for the sample app.
5. After a successful deployment, open the generated URL and check all eleven navigation pages and report downloads.

### Deployment notes

- The app uses a local SQLite database. Community Cloud filesystems are not a durable shared database: saved recommendation statuses can be lost when the app is rebuilt or restarted. For durable multi-user action tracking, move `recommendation_actions` to a managed PostgreSQL service and add authentication before using real business data.
- This demonstration has no authentication or role-based access (login is deferred). Do not upload confidential campaign/customer data to a public deployment. Use only data you are permitted to share.
- Power BI Desktop is separate from the hosted web app. Follow [Power BI setup](./powerbi/README.md) to create and publish a PBIX report in your own Power BI workspace.

## Data pipeline

```text
scripts/generate_data.py
        ↓
dataset/*.csv
        ↓
marketing_intelligence/data_pipeline.py
  cleaning + validation + SQLite loading
        ↓
dataset/marketing.sqlite3
        ↓
marketing_intelligence/analytics.py → app.py
```

The deployable app uses SQLite to avoid requiring a managed database for a portfolio demo. The generated project has 24 campaigns, 6 channels, 750 customers, 5,040 daily campaign activity rows, and roughly 1,700 conversions (exact deterministic counts are shown by the generator). Primary and foreign keys are enforced by [sql/schema.sql](./sql/schema.sql); [sql/mysql_schema.sql](./sql/mysql_schema.sql) is an optional MySQL 8.0+ migration starting point for a future shared deployment.

## Metric definitions

| Metric | Definition |
|---|---|
| CTR | Clicks ÷ impressions |
| CPC | Marketing spend ÷ clicks |
| CPA | Marketing spend ÷ conversions |
| Conversion rate | Conversions ÷ clicks |
| ROAS | Attributed conversion revenue ÷ marketing spend |
| Repeat customer rate | Converting customers with more than one conversion ÷ converting customers |

Zero denominators return zero in the app. Spend and conversion facts are aggregated independently before they are joined, preventing duplicated totals. Revenue is attributed to the campaign recorded on a conversion. ROAS and marketing return exclude product costs, overhead, and incrementality; they are not net profit or causal lift. The sample funnel can contain repeated customers and is not a deduplicated person-level journey.

## Validation and tests

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py marketing_intelligence scripts tests
```

See [product documentation](./product_documentation/) and [Power BI setup](./powerbi/README.md).
