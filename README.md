# CMS RCM MVP

24-hour public-data MVP for Medicare Advantage revenue-opportunity forecasting and prior-authorization intelligence.

This repo is intentionally scoped to official public CMS sources. The forecasting data is based on MA enrollment trends, so any revenue number should be treated as a documented proxy/opportunity estimate, not actual collections or remittance forecasting.

## Current Setup

- Project structure created.
- Core CMS raw data downloads are stored under `data/raw/`.
- Optional CPSC monthly enrollment ZIPs and Data.CMS reference links are stored under `data/raw/`.
- Python virtual environment uses `.venv/`.
- EDA, model, and dashboard code are intentionally not implemented yet.

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
