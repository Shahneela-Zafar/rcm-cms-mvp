# Notebook 02 EDA Visual Report

This GitHub-readable report was generated from `notebooks/02_ma_enrollment_eda.ipynb` because GitHub can fail to render large/output-heavy notebooks cleanly. The original notebook remains in the `notebooks/` folder with all code, cells, and outputs.

## Executive EDA Readout

- Source months loaded: 29
- Source rows preserved: 590,398
- Data window: 2024-01 to 2026-05
- National observed enrollment growth: 2,606,351 (7.79%)
- Average suppressed row share: 49.32%
- State/territory count: 56
- County key count: 3,268
- Plan type count: 10

## Graph Catalog

### 1. National observed MA enrollment trend

![National observed MA enrollment trend](assets/eda_02/01_national_enrollment_trend.png)

- Elements: `National observed MA enrollment trend` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows the core forecasting target over time.
- Result readout: Enrollment rises from about 33.48M to 36.08M across the public CMS window.

### 2. National month-over-month enrollment change

![National month-over-month enrollment change](assets/eda_02/02_national_mom_change.png)

- Elements: `National month-over-month enrollment change` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows short-term movement that affects forecast stability.
- Result readout: Most months are positive, with a few visible negative or lower-growth periods.

### 3. National MoM growth percentage

![National MoM growth percentage](assets/eda_02/03_national_mom_growth_pct.png)

- Elements: `National MoM growth percentage` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Normalizes monthly changes so growth intensity is easier to compare.
- Result readout: Growth is steady but not perfectly linear, which justifies comparing multiple simple forecast models.

### 4. Suppressed row share trend

![Suppressed row share trend](assets/eda_02/04_suppressed_share_trend.png)

- Elements: `Suppressed row share trend` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows how much source data has CMS suppression instead of numeric enrollment.
- Result readout: Suppression remains material at roughly half of rows, so rows are flagged rather than dropped.

### 5. Numeric vs suppressed rows by month

![Numeric vs suppressed rows by month](assets/eda_02/05_numeric_vs_suppressed_rows.png)

- Elements: `Numeric vs suppressed rows by month` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Separates usable numeric enrollment rows from CMS suppressed rows.
- Result readout: The source volume is stable, and suppressed rows are consistently large enough to require explicit handling.

### 6. Source rows by month

![Source rows by month](assets/eda_02/06_source_rows_by_month.png)

- Elements: `Source rows by month` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Checks whether monthly file volume is stable.
- Result readout: Monthly rows are stable, supporting time-series comparability.

### 7. Dimension coverage by month

![Dimension coverage by month](assets/eda_02/07_dimension_coverage.png)

- Elements: `Dimension coverage by month` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Confirms state, county, and plan-type coverage.
- Result readout: Coverage is stable enough for national and regional EDA.

### 8. Top states by absolute growth

![Top states by absolute growth](assets/eda_02/08_top_state_absolute_growth.png)

- Elements: `Top states by absolute growth` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Ranks markets by total added enrollment.
- Result readout: California and Texas lead the absolute opportunity story.

### 9. Lowest states by absolute growth

![Lowest states by absolute growth](assets/eda_02/09_lowest_state_absolute_growth.png)

- Elements: `Lowest states by absolute growth` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows where enrollment opportunity is weaker or negative.
- Result readout: Some smaller markets decline, so a growth strategy should not treat all states equally.

### 10. Top states by growth rate

![Top states by growth rate](assets/eda_02/10_top_state_growth_pct.png)

- Elements: `Top states by growth rate` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Controls for market size by using percentage growth.
- Result readout: High growth-rate markets can be useful sales targets even when absolute volume is smaller.

### 11. Largest states by latest enrollment

![Largest states by latest enrollment](assets/eda_02/11_top_state_latest_enrollment.png)

- Elements: `Largest states by latest enrollment` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows market scale independent of growth.
- Result readout: Large states remain strategic even when growth rate is moderate.

### 12. State growth volatility

![State growth volatility](assets/eda_02/12_state_growth_volatility.png)

- Elements: `State growth volatility` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Identifies markets where forecasts require more caution.
- Result readout: Volatile states should be monitored separately from stable high-growth states.

### 13. State scale vs growth rate

![State scale vs growth rate](assets/eda_02/13_state_scale_vs_growth.png)

- Elements: `State scale vs growth rate` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Combines market size and growth intensity.
- Result readout: Best sales targets usually sit toward the upper-right or have large bubble size.

### 14. Top states by average monthly growth

![Top states by average monthly growth](assets/eda_02/14_state_avg_mom_growth.png)

- Elements: `Top states by average monthly growth` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows persistent monthly growth, not just first-to-last change.
- Result readout: Average monthly growth highlights sustained momentum.

### 15. Top counties by absolute growth

![Top counties by absolute growth](assets/eda_02/15_top_county_absolute_growth.png)

- Elements: `Top counties by absolute growth` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Identifies county-level opportunity pockets.
- Result readout: Large metro counties dominate absolute enrollment lift.

### 16. Lowest counties by absolute growth

![Lowest counties by absolute growth](assets/eda_02/16_lowest_county_absolute_growth.png)

- Elements: `Lowest counties by absolute growth` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows county markets with weaker trend.
- Result readout: Declining counties are not ideal first targets for growth conversations.

### 17. Top counties by growth percentage

![Top counties by growth percentage](assets/eda_02/17_top_county_growth_pct.png)

- Elements: `Top counties by growth percentage` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Finds smaller but fast-growing markets after filtering tiny bases.
- Result readout: Rate-based opportunities can differ from absolute-volume opportunities.

### 18. County suppression hotspots

![County suppression hotspots](assets/eda_02/18_county_suppression_hotspots.png)

- Elements: `County suppression hotspots` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows where CMS suppression is most concentrated.
- Result readout: High-suppression counties need careful interpretation and should not be overfit.

### 19. Latest enrollment by plan type

![Latest enrollment by plan type](assets/eda_02/19_plan_type_latest_enrollment.png)

- Elements: `Latest enrollment by plan type` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows plan-type mix in the latest month.
- Result readout: HMO/HMOPOS and Local PPO dominate observed enrollment.

### 20. Plan type absolute growth

![Plan type absolute growth](assets/eda_02/20_plan_type_absolute_growth.png)

- Elements: `Plan type absolute growth` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows which plan types are driving growth.
- Result readout: HMO/HMOPOS is the largest growth contributor in the observed period.

### 21. Plan type growth percentage

![Plan type growth percentage](assets/eda_02/21_plan_type_growth_pct.png)

- Elements: `Plan type growth percentage` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Compares plan-type growth rates independent of size.
- Result readout: Some smaller plan types move sharply because their bases are smaller or periods differ.

### 22. Average plan-type enrollment share

![Average plan-type enrollment share](assets/eda_02/22_plan_type_avg_share.png)

- Elements: `Average plan-type enrollment share` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows concentration of enrollment by product type.
- Result readout: The market is concentrated in a few plan categories.

### 23. Missing/unusable value profile

![Missing/unusable value profile](assets/eda_02/23_missing_unusable_profile.png)

- Elements: `Missing/unusable value profile` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows which fields create data-quality risk.
- Result readout: Core dimensions are present; enrollment suppression is the main usability issue.

### 24. Duplicate business-key rows by month

![Duplicate business-key rows by month](assets/eda_02/24_duplicate_rows_by_month.png)

- Elements: `Duplicate business-key rows by month` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Checks repeated business keys before aggregation.
- Result readout: Duplicate summaries are documented so aggregation remains traceable.

### 25. Outlier flags summary

![Outlier flags summary](assets/eda_02/25_outlier_flags_summary.png)

- Elements: `Outlier flags summary` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows where unusual movement was found.
- Result readout: Outliers are most frequent at county level and are flagged, not dropped.

### 26. State outlier counts

![State outlier counts](assets/eda_02/26_state_outlier_counts.png)

- Elements: `State outlier counts` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows which states need extra review for monthly jumps.
- Result readout: A small set of states contributes many large MoM movements.

### 27. County outlier counts by state

![County outlier counts by state](assets/eda_02/27_county_outlier_counts.png)

- Elements: `County outlier counts by state` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Shows where county-level movement is most irregular.
- Result readout: County outlier review is important before making local-market claims.

### 28. Forecasting readiness coverage

![Forecasting readiness coverage](assets/eda_02/28_forecasting_readiness_coverage.png)

- Elements: `Forecasting readiness coverage` chart with relevant time, geography, plan-type, quality, or outlier dimensions.
- Why this step exists: Summarizes the data breadth used for forecasting.
- Result readout: The dataset has 29 months, 56 states/territories, 3,268 county keys, and 10 plan types.

## Handling Policy

- Missing/unusable values are profiled before modeling.
- CMS suppressed enrollment values are retained and flagged, not dropped.
- Duplicate business keys are summarized and handled through traceable aggregation.
- Outliers are flagged for review and retained in the modeling-ready tables.
- Forecasting uses observed numeric enrollment totals and clearly labels revenue as a PMPM proxy.