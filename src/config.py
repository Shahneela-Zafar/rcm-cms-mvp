from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
TABLE_DIR = REPORT_DIR / "tables"
FIGURE_DIR = REPORT_DIR / "figures"

MA_SCP_DIR = RAW_DIR / "ma_scp"
CPSC_DIR = RAW_DIR / "cpsc"

EXPECTED_START = "2024-01"
EXPECTED_END = "2026-05"

# EDA result: national observed enrollment increased 7.79% across 29 months.
# Use a transparent PMPM proxy assumption only for opportunity framing.
PMPM_PROXY_REVENUE = 115.0


def ensure_dirs() -> None:
    for path in [PROCESSED_DIR, MODEL_DIR, TABLE_DIR, FIGURE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

