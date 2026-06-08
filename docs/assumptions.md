# Assumptions

- Public CMS files used here support enrollment and market-opportunity analysis.
- They do not provide actual provider collections, ERA/835 payments, or request-level prior authorization labels.
- Revenue forecasting should be presented as proxy revenue or opportunity forecasting unless internal billing/remittance data is added.
- Prior authorization intelligence should be framed as risk prioritization aligned to CMS public reporting rules, not a production denial model.
- Forecast model selection uses 3-month holdout MAPE. The current best observed-enrollment model is `linear_drift`.
- Prophet remains included as a required modeling comparison, but the dashboard should not headline it unless future data improves its holdout performance.
- CPSC is analyzed at contract-plan and state-plan level. County-level CPSC expansion is intentionally avoided in notebooks because it creates very large intermediate tables; MA SCP already supports county-level opportunity analytics.
