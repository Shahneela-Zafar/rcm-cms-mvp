from __future__ import annotations

import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": textwrap.dedent(source).strip().splitlines(keepends=True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": textwrap.dedent(source).strip().splitlines(keepends=True),
    }


def write_notebook(name: str, cells: list[dict]) -> None:
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python (rcm-cms-mvp)", "language": "python", "name": "rcm-cms-mvp"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (NOTEBOOK_DIR / name).write_text(json.dumps(notebook, indent=1), encoding="utf-8")


common_setup = code(
    """
    from __future__ import annotations

    import json
    import re
    import zipfile
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import plotly.express as px

    pd.set_option("display.max_columns", 100)
    pd.set_option("display.max_rows", 100)
    pd.set_option("display.max_colwidth", 120)

    ROOT = Path.cwd()
    if ROOT.name == "notebooks":
        ROOT = ROOT.parent

    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from src.config import PROCESSED_DIR, TABLE_DIR, FIGURE_DIR, CPSC_DIR, PMPM_PROXY_REVENUE

    for path in [PROCESSED_DIR, TABLE_DIR, FIGURE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {ROOT}")
    """
)


forecast_cells = [
    md(
        """
        # 03 Revenue Opportunity Forecasting

        Purpose: build the 90-day forecast deliverable using the EDA-approved target. The EDA showed 29 monthly observations, 590,398 preserved source rows, and national observed enrollment growth of about 7.79%. Because the series is short, this notebook compares simple baselines against Prophet instead of assuming the most complex model is best.

        Decision from EDA: model `observed_enrollment` first, and derive `proxy_revenue` with the documented PMPM assumption. Do not call this actual collections forecasting.
        """
    ),
    common_setup,
    md(
        """
        ## Run Forecast Pipeline

        Why: the reusable module trains and evaluates all models consistently. It writes the same outputs the dashboard and validation notebook consume.
        """
    ),
    code(
        """
        from src.models.forecast_prophet import run_forecasting

        forecast_results, forecast_metrics = run_forecasting()
        display(forecast_metrics)
        """
    ),
    md(
        """
        ## Model Selection Decision

        Why: model selection must come from holdout performance, not preference. The last 3 months are used as the holdout window. Lower MAPE is better.
        """
    ),
    code(
        """
        best_models = forecast_metrics.sort_values(["target", "mape"]).groupby("target").head(1)
        display(best_models)
        print("Decision: use the best holdout-MAPE model for dashboard headline, while still showing all model metrics.")
        """
    ),
    md(
        """
        ## Forecast vs Actual: Holdout

        Elements: x-axis is month; y-axis is target value; colored lines are models; black markers are actual holdout values.

        Why: this shows whether the forecast method actually tracked the latest known months.
        """
    ),
    code(
        """
        for target in ["observed_enrollment", "proxy_revenue"]:
            holdout = forecast_results[(forecast_results["target"].eq(target)) & (forecast_results["period_type"].eq("holdout"))]
            fig = px.line(holdout, x="ds", y="yhat", color="model", markers=True, title=f"Holdout forecast comparison: {target}")
            actual = holdout.drop_duplicates("ds")[["ds", "actual"]]
            fig.add_scatter(x=actual["ds"], y=actual["actual"], mode="markers+lines", name="actual", marker=dict(color="black", size=10))
            fig.show()
        """
    ),
    md(
        """
        ## 90-Day Future Projection

        Elements: x-axis is forecast month; y-axis is predicted observed enrollment or proxy revenue; color is model.

        Why: the business deliverable asks for a 90-day projection. The MVP includes future predictions while keeping model comparison visible.
        """
    ),
    code(
        """
        for target in ["observed_enrollment", "proxy_revenue"]:
            future = forecast_results[(forecast_results["target"].eq(target)) & (forecast_results["period_type"].eq("future"))]
            fig = px.line(future, x="ds", y="yhat", color="model", markers=True, title=f"90-day future projection: {target}")
            fig.show()
            display(future.sort_values(["ds", "model"]))
        """
    ),
    md(
        """
        ## Forecasting Caveats

        - `observed_enrollment` uses numeric CMS rows only; suppressed rows are preserved elsewhere and flagged.
        - `proxy_revenue` equals observed enrollment multiplied by the documented PMPM proxy assumption.
        - Prophet is included, but on this short series the simpler linear drift baseline performs best. That is an acceptable result; complexity does not win by default.
        """
    ),
]


cpsc_cells = [
    md(
        """
        # 04 CPSC Plan-Level Analysis

        Purpose: use the optional CPSC files for plan/contract-level opportunity analysis. This is deeper than MA SCP because it includes contract and plan identifiers.

        Implementation decision: read the large CPSC enrollment CSVs in chunks. That avoids loading multi-gigabyte expanded CSV content into memory.
        """
    ),
    common_setup,
    md(
        """
        ## Chunked CPSC Aggregation

        Why: CPSC enrollment files are large. The first safe aggregation level for the MVP is contract-plan-month and state-plan-month, not raw county rows. County-level CPSC is too large for a notebook loop and is unnecessary for the current dashboard because MA SCP already covers county opportunity.
        """
    ),
    code(
        """
        def month_from_name(path: Path) -> str:
            match = re.search(r"(20\\d{2}-\\d{2})", path.name)
            if not match:
                raise ValueError(path.name)
            return match.group(1)


        def find_csv(zf: zipfile.ZipFile, contains: str) -> str:
            matches = [n for n in zf.namelist() if contains.lower() in n.lower() and n.lower().endswith(".csv")]
            if not matches:
                raise ValueError(f"No CSV containing {contains}")
            return matches[0]


        plan_rows = []
        state_plan_rows = []
        contract_rows = []
        zip_paths = sorted(CPSC_DIR.glob("*.zip"))

        for zip_path in zip_paths:
            month = month_from_name(zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                contract_csv = find_csv(zf, "Contract_Info")
                contract = pd.read_csv(zf.open(contract_csv), dtype=str, keep_default_na=False, encoding="cp1252")
                contract["report_month_label"] = month
                contract_rows.append(contract)

                enrollment_csv = find_csv(zf, "Enrollment_Info")
                chunks = pd.read_csv(
                    zf.open(enrollment_csv),
                    dtype=str,
                    keep_default_na=False,
                    encoding="cp1252",
                    chunksize=250_000,
                )
                for chunk in chunks:
                    chunk["Enrollment"] = pd.to_numeric(chunk["Enrollment"].str.replace(",", "", regex=False), errors="coerce")
                    chunk["report_month_label"] = month
                    plan_grouped = (
                        chunk.groupby(["report_month_label", "Contract Number", "Plan ID"], as_index=False)
                        .agg(observed_enrollment=("Enrollment", "sum"), source_rows=("Enrollment", "size"))
                    )
                    state_plan_grouped = (
                        chunk.groupby(["report_month_label", "Contract Number", "Plan ID", "State"], as_index=False)
                        .agg(observed_enrollment=("Enrollment", "sum"), source_rows=("Enrollment", "size"), counties=("FIPS State County Code", "nunique"))
                    )
                    plan_rows.append(plan_grouped)
                    state_plan_rows.append(state_plan_grouped)

        cpsc_plan_monthly = pd.concat(plan_rows, ignore_index=True)
        cpsc_plan_monthly = (
            cpsc_plan_monthly.groupby(["report_month_label", "Contract Number", "Plan ID"], as_index=False)
            .agg(observed_enrollment=("observed_enrollment", "sum"), source_rows=("source_rows", "sum"))
        )
        cpsc_state_plan_monthly = pd.concat(state_plan_rows, ignore_index=True)
        cpsc_state_plan_monthly = (
            cpsc_state_plan_monthly.groupby(["report_month_label", "Contract Number", "Plan ID", "State"], as_index=False)
            .agg(observed_enrollment=("observed_enrollment", "sum"), source_rows=("source_rows", "sum"), counties=("counties", "max"))
        )
        cpsc_contract = pd.concat(contract_rows, ignore_index=True)

        cpsc_plan_monthly.to_parquet(PROCESSED_DIR / "cpsc_plan_monthly.parquet", index=False)
        cpsc_state_plan_monthly.to_parquet(PROCESSED_DIR / "cpsc_state_plan_monthly.parquet", index=False)
        cpsc_contract.to_parquet(PROCESSED_DIR / "cpsc_contract_info_monthly.parquet", index=False)
        print(f"CPSC contract-plan monthly rows after aggregation: {len(cpsc_plan_monthly):,}")
        print(f"CPSC state-plan monthly rows after aggregation: {len(cpsc_state_plan_monthly):,}")
        print(f"CPSC contract rows: {len(cpsc_contract):,}")
        """
    ),
    md("## Contract/Plan Growth Summary\n\nWhy: this identifies high-growth plans and contracts for RCM sales targeting."),
    code(
        """
        plan_monthly = pd.read_parquet(PROCESSED_DIR / "cpsc_plan_monthly.parquet")
        plan_monthly["report_month"] = pd.PeriodIndex(plan_monthly["report_month_label"], freq="M").to_timestamp()
        plan_monthly = plan_monthly.sort_values(["Contract Number", "Plan ID", "report_month"])

        plan_growth = (
            plan_monthly.groupby(["Contract Number", "Plan ID"], as_index=False)
            .agg(
                first_month=("report_month_label", "first"),
                last_month=("report_month_label", "last"),
                months_present=("report_month_label", "nunique"),
                first_enrollment=("observed_enrollment", "first"),
                last_enrollment=("observed_enrollment", "last"),
                source_rows=("source_rows", "sum"),
            )
        )
        plan_growth["absolute_growth"] = plan_growth["last_enrollment"] - plan_growth["first_enrollment"]
        plan_growth["growth_pct"] = np.where(plan_growth["first_enrollment"] > 0, plan_growth["absolute_growth"] / plan_growth["first_enrollment"], np.nan)

        latest_contract = cpsc_contract.sort_values("report_month_label").groupby(["Contract ID", "Plan ID"], as_index=False).tail(1)
        plan_growth = plan_growth.merge(
            latest_contract[["Contract ID", "Plan ID", "Organization Name", "Plan Name", "Plan Type", "Parent Organization"]],
            left_on=["Contract Number", "Plan ID"],
            right_on=["Contract ID", "Plan ID"],
            how="left",
        ).sort_values(["absolute_growth", "last_enrollment"], ascending=False)

        plan_monthly.to_parquet(PROCESSED_DIR / "cpsc_plan_monthly.parquet", index=False)
        plan_growth.to_csv(TABLE_DIR / "cpsc_plan_growth.csv", index=False)
        display(plan_growth.head(25))
        """
    ),
    md("## CPSC Visual Results\n\nElements: bars show absolute growth; color shows plan type where available. These are optional deeper sales leads beyond the national forecast."),
    code(
        """
        top_plans = plan_growth.head(20).copy()
        top_plans["plan_label"] = top_plans["Contract Number"] + "-" + top_plans["Plan ID"]
        fig = px.bar(top_plans, x="plan_label", y="absolute_growth", color="Plan Type", hover_name="Plan Name", title="Top CPSC Plans by Absolute Enrollment Growth")
        fig.show()

        plan_growth_scatter = plan_growth.replace([np.inf, -np.inf], np.nan).dropna(subset=["growth_pct"]).head(500).copy()
        plan_growth_scatter["abs_growth_for_marker"] = plan_growth_scatter["absolute_growth"].abs().clip(lower=1)
        fig = px.scatter(
            plan_growth_scatter,
            x="last_enrollment",
            y="growth_pct",
            size="abs_growth_for_marker",
            hover_name="Plan Name",
            color="Plan Type",
            title="CPSC Plan Scale vs Growth",
        )
        fig.show()

        state_plan = pd.read_parquet(PROCESSED_DIR / "cpsc_state_plan_monthly.parquet")
        latest_month = state_plan["report_month_label"].max()
        latest_state_plan = (
            state_plan[state_plan["report_month_label"].eq(latest_month)]
            .groupby("State", as_index=False)
            .agg(observed_enrollment=("observed_enrollment", "sum"), plans=("Plan ID", "nunique"))
            .sort_values("observed_enrollment", ascending=False)
            .head(25)
        )
        latest_state_plan.to_csv(TABLE_DIR / "cpsc_latest_state_summary.csv", index=False)
        fig = px.bar(latest_state_plan, x="State", y="observed_enrollment", title=f"CPSC Latest Enrollment by State ({latest_month})")
        fig.show()
        """
    ),
]


pa_cells = [
    md(
        """
        # 05 Prior Authorization Risk Scoring Demo

        Purpose: create a CMS-aligned PA risk prioritization prototype. Public CMS PA artifacts provide reporting schema and policy timing rules, not mature request-level labels. Therefore this notebook uses a seeded demo dataset plus transparent rule features.
        """
    ),
    common_setup,
    md("## Run PA Demo Model\n\nWhy: the model demonstrates feature engineering and classifier workflow while staying honest about public-data limits."),
    code(
        """
        from src.models.pa_classifier import run_pa_model

        pa_predictions, pa_metrics = run_pa_model()
        display(pa_metrics)
        display(pa_predictions.sort_values("hybrid_denial_risk", ascending=False).head(20))
        """
    ),
    md("## PA Risk Visuals\n\nElements: histograms show risk distribution; bars show high-risk groups by procedure/payer."),
    code(
        """
        fig = px.histogram(pa_predictions, x="hybrid_denial_risk", color="hybrid_risk_bucket", title="PA Hybrid Denial Risk Distribution")
        fig.show()

        risk_by_proc = (
            pa_predictions.groupby(["procedure_type", "payer_type"], as_index=False)
            .agg(avg_hybrid_denial_risk=("hybrid_denial_risk", "mean"), high_risk_cases=("hybrid_risk_bucket", lambda s: int((s == "high").sum())))
            .sort_values("avg_hybrid_denial_risk", ascending=False)
        )
        risk_by_proc.to_csv(TABLE_DIR / "pa_risk_by_procedure_payer.csv", index=False)
        fig = px.bar(risk_by_proc, x="procedure_type", y="avg_hybrid_denial_risk", color="payer_type", title="Average PA Denial Risk by Procedure and Payer")
        fig.show()
        display(risk_by_proc)
        """
    ),
    md(
        """
        ## PA Decision

        The model accuracy is useful for demonstration, but the correct business framing is risk prioritization. The output tells a team which authorization requests need stronger documentation before submission; it does not claim payer-specific production denial prediction.
        """
    ),
]


validation_cells = [
    md("# 06 Model Evaluation And Validation\n\nPurpose: collect model quality, data-quality policy, and MVP limitations into one validation notebook."),
    common_setup,
    code(
        """
        from src.models.evaluate import compile_validation_summary

        validation = compile_validation_summary()
        display(validation)
        """
    ),
    md("## Forecast Metrics\n\nWhy: compare all models, not just the selected model. This prevents overclaiming."),
    code(
        """
        forecast_metrics = pd.read_csv(TABLE_DIR / "forecast_metrics.csv")
        display(forecast_metrics)
        fig = px.bar(forecast_metrics, x="model", y="mape", color="target", barmode="group", title="Forecast Holdout MAPE by Model")
        fig.show()
        """
    ),
    md("## PA Metrics\n\nWhy: classifier quality is reported separately from the public-data caveat."),
    code(
        """
        pa_metrics = pd.read_csv(TABLE_DIR / "pa_model_metrics.csv")
        cm = pd.read_csv(TABLE_DIR / "pa_confusion_matrix.csv", index_col=0)
        display(pa_metrics)
        display(cm)
        """
    ),
    md("## Data Quality Policy\n\nWhy: this MVP keeps data-quality decisions explicit: suppressed rows and outliers are flagged, not deleted."),
    code(
        """
        display(pd.read_csv(TABLE_DIR / "ma_scp_missing_value_profile.csv"))
        display(pd.read_csv(TABLE_DIR / "ma_scp_outlier_handling_summary.csv"))
        """
    ),
]


dashboard_asset_cells = [
    md("# 07 Dashboard Export Assets\n\nPurpose: prepare compact tables that the Streamlit dashboard can load quickly and reviewers can inspect."),
    common_setup,
    code(
        """
        forecast = pd.read_csv(PROCESSED_DIR / "forecast_results.csv", parse_dates=["ds"])
        metrics = pd.read_csv(TABLE_DIR / "forecast_metrics.csv")
        state_growth = pd.read_csv(TABLE_DIR / "ma_scp_state_growth.csv")
        pa = pd.read_csv(PROCESSED_DIR / "pa_predictions.csv")
        delay = pd.read_csv(PROCESSED_DIR / "delay_predictions.csv")

        best_models = metrics.sort_values(["target", "mape"]).groupby("target").head(1)
        dashboard_forecast_summary = forecast[forecast["period_type"].isin(["holdout", "future"])].copy()
        dashboard_state_opportunities = state_growth.head(30).copy()
        dashboard_pa_summary = (
            pa.groupby(["procedure_type", "payer_type", "hybrid_risk_bucket"], as_index=False)
            .agg(cases=("hybrid_denial_risk", "size"), avg_denial_risk=("hybrid_denial_risk", "mean"))
            .sort_values("avg_denial_risk", ascending=False)
        )
        dashboard_delay_summary = (
            delay.groupby(["procedure_type", "payer_type", "risk_bucket"], as_index=False)
            .agg(combinations=("delay_risk_score", "size"), avg_delay_risk=("delay_risk_score", "mean"), delay_flags=("delay_flag", "sum"))
            .sort_values(["delay_flags", "avg_delay_risk"], ascending=False)
        )

        dashboard_forecast_summary.to_csv(TABLE_DIR / "dashboard_forecast_summary.csv", index=False)
        dashboard_state_opportunities.to_csv(TABLE_DIR / "dashboard_state_opportunities.csv", index=False)
        dashboard_pa_summary.to_csv(TABLE_DIR / "dashboard_pa_summary.csv", index=False)
        dashboard_delay_summary.to_csv(TABLE_DIR / "dashboard_delay_summary.csv", index=False)
        best_models.to_csv(TABLE_DIR / "dashboard_best_models.csv", index=False)

        display(best_models)
        display(dashboard_state_opportunities.head())
        display(dashboard_pa_summary.head())
        display(dashboard_delay_summary.head())
        """
    ),
    md("## Dashboard Asset Decision\n\nThe dashboard should load compact CSV summaries plus the forecast result table. The full long MA SCP table stays as Parquet for modeling, not dashboard rendering."),
]


def main() -> None:
    write_notebook("03_revenue_opportunity_forecasting.ipynb", forecast_cells)
    write_notebook("04_cpsc_plan_level_analysis.ipynb", cpsc_cells)
    write_notebook("05_prior_auth_risk_scoring_demo.ipynb", pa_cells)
    write_notebook("06_model_evaluation_and_validation.ipynb", validation_cells)
    write_notebook("07_dashboard_export_assets.ipynb", dashboard_asset_cells)


if __name__ == "__main__":
    main()
