# Research and Development Notes

This document explains how the MVP was built, why specific decisions were made, what was validated, and where the project should go next.

## Problem Framing

The original objective was to build a 24-hour MVP for:

- Revenue forecasting
- Prior authorization prediction
- Auth delay prediction
- Growth opportunity analytics
- Executive BI dashboard

Because the project uses public CMS data, the system cannot truthfully claim access to provider-specific collections, remittance, payer adjudication, or request-level prior authorization decisions. The MVP therefore frames revenue as an opportunity proxy and PA as risk prioritization.

## Data Sources

Primary public sources:

- CMS Medicare Advantage monthly state/county/plan-type enrollment files.
- CMS Medicare Advantage plan directory and benefit-related files.
- CMS prior authorization reporting template and CMS-0057-F related policy material.
- CMS Medicare Advantage step therapy memo.

Optional public source:

- CPSC monthly enrollment by contract, plan, state, and county.

The project deliberately avoids gated data, private payer files, PHI, claim lines, or customer-specific RCM exports.

## Data Handling Decisions

### Suppressed CMS Values

CMS suppresses some small-cell enrollment values. Those rows were retained and flagged instead of dropped. This keeps row lineage intact and prevents the model from hiding uncertainty.

### Missing Values

Missingness was profiled before modeling. The MVP avoids blind imputation for public CMS suppression because doing so could create false precision.

### Duplicates

Duplicates were checked at source-key and reporting-month levels. Aggregations were performed after key normalization so monthly national, state, county, and plan summaries remained traceable.

### Outliers

Outliers were flagged, not removed. This is important because public enrollment changes can reflect real market movement, contract changes, reporting shifts, or geography-specific enrollment jumps.

## EDA Summary

Notebook `02_ma_enrollment_eda.ipynb` performs the deep enrollment EDA:

- Source file coverage
- Month coverage
- State and county coverage
- Suppression share
- Missingness patterns
- Duplicate checks
- National trend
- State growth
- County growth
- Plan-type movement
- Outlier flags
- Modeling readiness checks

The main result is that the public CMS MA enrollment trend is usable for opportunity forecasting, but it must be explained as enrollment-driven and not as actual revenue.

## Forecasting Approach

Forecast target:

- `observed_enrollment`

Revenue proxy:

- `proxy_revenue = observed_enrollment * 115 PMPM`

Models evaluated:

- Naive last value
- 3-month moving average
- Linear drift
- Prophet
- Exponential smoothing
- Optional LSTM path reserved for extended experimentation

Holdout design:

- Last 3 months used as holdout.
- Metrics include MAE, RMSE, and MAPE.

Decision:

- `linear_drift` won the observed-enrollment holdout benchmark.
- Prophet remains useful as a benchmark, but it was not selected as the headline model because the time series is short and simple trend behavior dominated.

Why this is defensible:

- The MVP has only 29 monthly observations.
- Heavy models can overfit or underperform on short histories.
- The dashboard transparently shows all benchmark results instead of hiding underperforming models.

## Prior Authorization Risk Prototype

Public CMS reporting/policy data does not provide request-level PA outcome labels for a provider. Therefore, the MVP uses a CMS-aligned demo classifier based on:

- Procedure type
- Diagnosis category
- Payer type
- Historical approval-rate assumptions
- Step therapy flag
- Documentation score
- Prior denial history

Model:

- Gradient boosting classifier

Output:

- Denial-risk score
- Risk bucket
- Documentation strengthening recommendation

Interpretation:

- This is a prioritization prototype.
- It should not be sold as a production payer-specific denial predictor without real request-level historical outcomes.

## Auth Delay Risk

The delay module converts CMS timing expectations into operational risk flags:

- Expedited decision limit: 72 hours
- Standard decision limit: 7 calendar days

The model scores procedure-payer-urgency combinations and flags high-risk combinations for pre-submission review.

## Growth Opportunity Analytics

Growth opportunity is derived from:

- State-level MA enrollment growth
- County and plan-type summaries
- Optional CPSC plan/contract growth

The dashboard supports sales conversation starters:

- Which states are growing fastest?
- Which markets have the largest enrollment lift?
- Which plans/contracts show meaningful growth?
- Where should an RCM vendor prioritize outreach?

## Dashboard Design Decision

The dashboard was rebuilt around deliverables rather than implementation artifacts.

Final dashboard tabs:

- Executive View
- 90-Day Forecast
- Growth Opportunity
- Prior Auth Intelligence
- Auth Delay Risk
- Plan Intelligence
- Validation

This layout answers business questions first, while still exposing validation and assumptions.

## Validation

Validation outputs include:

- Forecast holdout metrics
- PA demo model metrics
- Delay-risk threshold assumptions
- Data-quality assumptions
- Public-data limitations

Key guardrails:

- Forecast is enrollment-based opportunity forecasting.
- Proxy revenue is not actual collections.
- PA model is a demo risk-prioritization model.
- Suppressed rows are retained and flagged.
- Outliers are reviewed rather than blindly removed.

## Known Limitations

- No private claims data.
- No actual collections data.
- No payer-specific request-level PA labels.
- Short time-series history.
- Public reporting has suppression and schema limitations.

## Recommended Next Steps

1. Add real client RCM data when available: charges, payments, adjustments, denials, appeals, and PA outcomes.
2. Replace demo PA labels with true historical authorization outcomes.
3. Add provider specialty and CPT-level feature engineering.
4. Expand forecast granularity by geography and specialty once reliable specialty-level payment files are integrated.
5. Add automated tests for pipeline outputs and dashboard data contracts.
6. Convert `PPT.md` into a designed PowerPoint deck for stakeholder presentation.
