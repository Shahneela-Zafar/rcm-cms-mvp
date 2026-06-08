# Validation Checklist

- Confirm all downloaded ZIP/PDF files are non-empty.
- Confirm core and optional ZIP files open successfully.
- Parse at least one monthly MA enrollment ZIP before modeling.
- Compare forecast model against a simple naive baseline.
- Label revenue outputs as proxy/opportunity estimates.
- Label PA outputs as risk prioritization unless real request-level labels are added.
- Verify the virtual environment imports `pandas`, `scikit-learn`, `prophet`, `streamlit`, and optional `tensorflow`.
- Confirm `scripts/run_pipeline.ps1` completes.
- Confirm notebooks `03` through `07` execute after `02`.
- Confirm dashboard starts with `scripts/run_dashboard.ps1`.
