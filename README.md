# CMS RCM MVP

24-hour public-data MVP for Medicare Advantage revenue-opportunity forecasting and prior-authorization intelligence.

This repo is intentionally scoped to official public CMS sources. The forecasting data is based on MA enrollment trends, so any revenue number should be treated as a documented proxy/opportunity estimate, not actual collections or remittance forecasting.

## Current Setup

- Project structure created.
- Core CMS raw data downloads are stored under `data/raw/`.
- Optional CPSC monthly enrollment ZIPs and Data.CMS reference links are stored under `data/raw/`.
- Python virtual environment uses `.venv/`.
- EDA, forecasting, PA risk scoring, delay scoring, validation, CPSC analysis, and dashboard code are implemented.

## MVP Decisions

- Forecasting target: `observed_enrollment` from CMS MA SCP files.
- Revenue framing: `proxy_revenue = observed_enrollment * 115 PMPM`; this is an opportunity proxy, not actual collections.
- Best forecast model from 3-month holdout: `linear_drift`, with observed-enrollment MAPE about `0.048%`.
- Prophet is included and evaluated, but it is not the headline model because it underperformed the simple baseline on this short 29-month series.
- CMS-suppressed enrollment rows are retained and flagged; they are not dropped.
- PA intelligence is framed as CMS-aligned risk prioritization using seeded demo labels, not production payer benchmarking.
- Delay risk uses CMS timing rules: 72 hours for expedited and 7 calendar days for standard requests.

## Environment

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r .\requirements.txt
python -m pip install -r .\requirements-optional.txt
```

`requirements-optional.txt` contains TensorFlow for the optional LSTM path.

## Data Download

From this folder:

```powershell
.\scripts\download_data.ps1
.\scripts\download_optional_data.ps1
```

The core script downloads:

- MA plan directory
- MA state/county penetration
- 2026 PBP benefits JSON
- CMS prior authorization reporting template
- CMS-0057-F final rule
- MA step therapy memo
- Monthly MA enrollment by state/county/plan type, January 2024 through May 2026

The optional script downloads:

- Monthly enrollment by contract/plan/state/county, January 2024 through May 2026
- Data dictionaries and source links for later Data.CMS manual/API exports

## Run Pipeline

```powershell
.\scripts\run_pipeline.ps1
```

This runs:

- MA SCP ingestion
- Forecast model evaluation
- PA risk scoring demo
- Auth delay risk scoring
- Validation summary compilation

## Run Dashboard

```powershell
.\scripts\run_dashboard.ps1
```

## Notebooks

- `01_data_inventory_and_quality.ipynb`: raw data integrity and coverage
- `02_ma_enrollment_eda.ipynb`: deep EDA, missing/duplicate/outlier handling, 24 graphs
- `03_revenue_opportunity_forecasting.ipynb`: baseline, Prophet, exponential smoothing, 90-day projection
- `04_cpsc_plan_level_analysis.ipynb`: optional CPSC plan/contract growth analysis with chunked aggregation
- `05_prior_auth_risk_scoring_demo.ipynb`: CMS-aligned PA denial-risk prototype
- `06_model_evaluation_and_validation.ipynb`: final validation and limitations
- `07_dashboard_export_assets.ipynb`: dashboard-ready CSV assets
