# Revenue Forecasting & Prior Authorization Intelligence

Slide-style summary for presentation, viva, interview, or stakeholder demo.

---

## 1. Project Title

Revenue Forecasting & Prior Authorization Intelligence

An RCM analytics MVP built with public CMS Medicare Advantage data.

---

## 2. Client Hook

We tell RCM teams what the next 90 days of collections opportunity may look like and which prior authorization requests are likely to be denied or delayed, so documentation can be strengthened before submission.

---

## 3. Business Problems Covered

- Revenue forecasting
- Prior authorization denial-risk prediction
- Auth delay risk
- Growth opportunity analytics
- Executive BI reporting

---

## 4. Data Sources

- CMS Medicare Advantage monthly state/county/plan-type enrollment files
- CMS MA plan directory and benefits-related files
- CMS prior authorization reporting template
- CMS-0057-F policy material
- CMS MA step therapy memo
- Optional CPSC plan/contract/state/county enrollment files

All sources are public CMS data.

---

## 5. Core MVP Deliverables

- 90-day forecast dashboard
- Prior authorization strengthening queue
- Auth delay risk queue
- Growth opportunity heatmap
- Plan-level sales intelligence
- Validation and assumptions summary

---

## 6. Forecasting Approach

Forecast target:

- Observed Medicare Advantage enrollment

Revenue proxy:

- Observed enrollment multiplied by 115 PMPM

Models evaluated:

- Naive last value
- Moving average
- Linear drift
- Prophet
- Exponential smoothing

---

## 7. Forecasting Result

Best holdout model:

- Linear drift

Why:

- Short 29-month public CMS history
- Simple trend baseline outperformed heavier alternatives
- Dashboard still shows full model benchmark for transparency

---

## 8. Prior Authorization Intelligence

The PA module creates a risk-prioritization queue using:

- Procedure type
- Diagnosis category
- Payer type
- Documentation score
- Step therapy flag
- Historical approval-rate assumptions
- Prior denial history

Output:

- Denial-risk score
- Risk bucket
- Documentation recommendation

---

## 9. Auth Delay Risk

The delay module flags procedure-payer combinations likely to exceed:

- 72 hours for expedited requests
- 7 calendar days for standard requests

Purpose:

- Identify requests that need pre-submission attention.

---

## 10. Growth Opportunity Analytics

The growth module identifies:

- High-growth states
- High-scale markets
- Plan and contract growth signals
- Sales conversation starters for RCM outreach

---

## 11. Dashboard

Tabs:

- Executive View
- 90-Day Forecast
- Growth Opportunity
- Prior Auth Intelligence
- Auth Delay Risk
- Plan Intelligence
- Validation

The dashboard is organized around business deliverables, not raw pipeline steps.

---

## 12. Validation

Validation includes:

- Forecast MAE, RMSE, MAPE
- PA demo accuracy and ROC AUC
- Data quality checks
- Suppression handling
- Outlier policy
- Scope limitations

---

## 13. Important Guardrails

- Revenue is an opportunity proxy, not actual collections.
- Public CMS data does not include provider-specific claim payments.
- PA prediction is a demo risk-prioritization model unless real PA outcomes are added.
- Suppressed rows are retained and flagged.
- Outliers are reviewed, not automatically dropped.

---

## 14. Tech Stack

- Python
- pandas
- scikit-learn
- Prophet
- statsmodels
- Streamlit
- Plotly
- Jupyter
- PowerShell automation

---

## 15. Final Outcome

The MVP demonstrates how public CMS data can support an RCM-facing intelligence product:

- Forecast opportunity
- Prioritize risky authorizations
- Flag delay risk
- Identify growth markets
- Present findings in an executive dashboard
