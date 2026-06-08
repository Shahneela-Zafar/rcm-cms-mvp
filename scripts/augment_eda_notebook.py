from __future__ import annotations

import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebooks" / "02_ma_enrollment_eda.ipynb"


def md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": textwrap.dedent(source).strip().splitlines(keepends=True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": textwrap.dedent(source).strip().splitlines(keepends=True),
    }


missing_duplicate_outlier_cells = [
    md(
        """
        ## Missing, Duplicate, And Outlier Handling

        Reason: EDA should not only describe the data; it should make data-quality decisions explicit. For this MVP, the policy is conservative:

        - Missing/suppressed enrollment is retained as source data.
        - Numeric modeling tables use observed numeric enrollment and carry suppression flags.
        - Duplicate source keys are profiled instead of blindly removed.
        - Outliers are flagged for model review, not deleted.

        This preserves CMS source fidelity while still producing model-ready tables.
        """
    ),
    code(
        """
        # Missing/null handling policy.
        # CMS uses "." for suppressed enrollment. Because that is meaningful,
        # the notebook keeps those rows and creates imputation-ready alternatives.
        missing_profile = pd.DataFrame(
            {
                "field": [
                    "state",
                    "county",
                    "plan_type",
                    "fips_code",
                    "enrolled_raw",
                    "enrolled",
                ],
                "missing_or_unusable_rows": [
                    int((~ma["has_state"]).sum()),
                    int((~ma["has_county"]).sum()),
                    int((~ma["has_plan_type"]).sum()),
                    int((~ma["has_fips"]).sum()),
                    int((ma["enrolled_raw"].eq("")).sum()),
                    int((ma["enrolled"].isna()).sum()),
                ],
            }
        )
        missing_profile["row_share"] = missing_profile["missing_or_unusable_rows"] / len(ma)

        # Do not replace source enrollment. Create analysis variants instead.
        ma["enrolled_observed_filled_zero"] = ma["enrolled"].fillna(0)
        ma["enrolled_missing_reason"] = np.select(
            [
                ma["is_enrollment_suppressed"],
                ma["is_enrollment_blank"],
                ma["enrolled"].isna(),
            ],
            [
                "cms_suppressed_dot",
                "blank",
                "non_numeric",
            ],
            default="numeric",
        )

        missing_profile.to_csv(REPORT_TABLE_DIR / "ma_scp_missing_value_profile.csv", index=False)
        display(missing_profile)
        display(ma["enrolled_missing_reason"].value_counts(dropna=False).rename_axis("reason").reset_index(name="rows"))
        """
    ),
    md(
        """
        ### Duplicate Handling

        A duplicate key means the same month/state/county/FIPS/plan-type appears more than once. We should not drop these rows automatically because duplicates may reflect source quirks, jurisdiction labels, or CMS file structure. The notebook profiles them so ingestion code can decide later whether aggregation is enough or whether manual review is needed.
        """
    ),
    code(
        """
        duplicate_keys = ["report_month", "state", "county", "fips_code_raw", "plan_type"]
        ma["is_duplicate_business_key"] = ma.duplicated(duplicate_keys, keep=False)

        duplicate_summary = (
            ma.loc[ma["is_duplicate_business_key"]]
            .groupby(duplicate_keys, as_index=False)
            .agg(
                duplicate_rows=("source_row_number", "count"),
                numeric_rows=("is_enrollment_numeric", "sum"),
                suppressed_rows=("is_enrollment_suppressed", "sum"),
                observed_enrollment_sum=("enrolled", "sum"),
                source_zips=("source_zip", lambda s: "; ".join(sorted(set(s)))),
            )
            .sort_values(["duplicate_rows", "observed_enrollment_sum"], ascending=False)
        )

        duplicate_summary.to_csv(REPORT_TABLE_DIR / "ma_scp_duplicate_business_key_summary.csv", index=False)
        print(f"Duplicate business-key rows: {int(ma['is_duplicate_business_key'].sum()):,}")
        display(duplicate_summary.head(25))
        """
    ),
    md(
        """
        ### Outlier Handling

        Outliers are calculated from month-over-month change. The goal is not to delete them. The goal is to create flags that the forecasting notebook can use for review, sensitivity testing, or robust baselines.

        The notebook uses an IQR rule: values outside Q1 - 1.5*IQR or Q3 + 1.5*IQR are flagged.
        """
    ),
    code(
        """
        def add_iqr_outlier_flag(df: pd.DataFrame, value_col: str, group_col: str | None = None) -> pd.DataFrame:
            out = df.copy()
            out[f"{value_col}_is_outlier_iqr"] = False
            out[f"{value_col}_iqr_lower"] = np.nan
            out[f"{value_col}_iqr_upper"] = np.nan

            groups = [(None, out)] if group_col is None else out.groupby(group_col, dropna=False)
            for key, group in groups:
                values = group[value_col].dropna()
                if len(values) < 4:
                    continue
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                idx = group.index
                out.loc[idx, f"{value_col}_iqr_lower"] = lower
                out.loc[idx, f"{value_col}_iqr_upper"] = upper
                out.loc[idx, f"{value_col}_is_outlier_iqr"] = (group[value_col] < lower) | (group[value_col] > upper)
            return out


        monthly_outlier_flags = add_iqr_outlier_flag(monthly, "mom_change")
        state_outlier_flags = add_iqr_outlier_flag(state_monthly.dropna(subset=["mom_change"]), "mom_change", "state")
        county_outlier_flags = add_iqr_outlier_flag(county_monthly.dropna(subset=["mom_change"]), "mom_change", "state_county_key")

        monthly_outlier_flags.to_csv(REPORT_TABLE_DIR / "ma_scp_national_outlier_flags.csv", index=False)
        state_outlier_flags.to_csv(REPORT_TABLE_DIR / "ma_scp_state_outlier_flags.csv", index=False)
        county_outlier_flags.to_csv(REPORT_TABLE_DIR / "ma_scp_county_outlier_flags.csv", index=False)

        outlier_handling_summary = pd.DataFrame(
            [
                {
                    "level": "national_monthly",
                    "rows_evaluated": len(monthly_outlier_flags),
                    "iqr_outliers": int(monthly_outlier_flags["mom_change_is_outlier_iqr"].sum()),
                    "action": "flag_only_keep_rows",
                },
                {
                    "level": "state_monthly",
                    "rows_evaluated": len(state_outlier_flags),
                    "iqr_outliers": int(state_outlier_flags["mom_change_is_outlier_iqr"].sum()),
                    "action": "flag_only_keep_rows",
                },
                {
                    "level": "county_monthly",
                    "rows_evaluated": len(county_outlier_flags),
                    "iqr_outliers": int(county_outlier_flags["mom_change_is_outlier_iqr"].sum()),
                    "action": "flag_only_keep_rows",
                },
            ]
        )
        outlier_handling_summary.to_csv(REPORT_TABLE_DIR / "ma_scp_outlier_handling_summary.csv", index=False)
        display(outlier_handling_summary)
        """
    ),
]


visual_cells = [
    md(
        """
        ## Visual EDA Gallery: 20+ Graphs

        Each graph is intentionally tied to a modeling or business question. The visual elements are:

        - X-axis: usually time, geography, plan type, or enrollment scale.
        - Y-axis: enrollment, growth, row count, or data-quality metric.
        - Color: category separation such as plan type or state.
        - Marker size: magnitude, only when non-negative.
        - Hover labels: exact values for review.

        The notebook writes these graphs inline. The interpretation below each chart is meant to be read before moving into forecasting.
        """
    ),
    code(
        """
        def explain(title: str, elements: str, readout: str) -> None:
            print(f"GRAPH: {title}")
            print(f"Elements: {elements}")
            print(f"Read the result as: {readout}")
            print("-" * 100)


        latest_month = monthly["report_month"].max()
        latest_label = monthly.loc[monthly["report_month"].eq(latest_month), "report_month_label"].iloc[0]
        top_10_states = state_growth.head(10)["state"].tolist()
        top_8_plan_types = first_last_plan.head(8)["plan_type"].tolist()
        """
    ),
    md(
        """
        ### Graph 1: National Observed Enrollment Trend

        Elements: x-axis is month; y-axis is observed enrollment; each marker is one CMS monthly file.

        Why: this is the first forecasting target because it is the most stable aggregate series.
        """
    ),
    code(
        """
        explain(
            "National Observed Enrollment Trend",
            "Line = month-to-month enrollment path; markers = available CMS months; y-axis = observed numeric enrollment.",
            "An upward line supports a growth/opportunity forecast. Sudden jumps should be reviewed before modeling.",
        )
        fig = px.line(monthly, x="report_month", y="observed_enrollment", markers=True, title="1. National Observed MA Enrollment")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 2: National Month-over-Month Change

        Elements: x-axis is month; y-axis is absolute enrollment change from the previous month.

        Why: forecasting models need to know whether changes are smooth or jumpy.
        """
    ),
    code(
        """
        explain(
            "National Month-over-Month Change",
            "Bars above zero = growth; bars below zero = decline; height = enrollment change from prior month.",
            "Large bars indicate periods that may dominate model fit or require explanation in the dashboard.",
        )
        fig = px.bar(monthly.dropna(subset=["mom_change"]), x="report_month", y="mom_change", title="2. National Month-over-Month Enrollment Change")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 3: National Month-over-Month Growth Rate

        Elements: x-axis is month; y-axis is percentage growth from the previous month.

        Why: percentage movement helps compare change magnitude across time independent of total scale.
        """
    ),
    code(
        """
        explain(
            "National MoM Growth Rate",
            "Line = percentage growth; zero line separates expansion from contraction.",
            "Consistent positive rates imply a smoother forecast; volatile rates suggest using baseline comparisons.",
        )
        fig = px.line(monthly.dropna(subset=["mom_growth_pct"]), x="report_month", y="mom_growth_pct", markers=True, title="3. National MoM Growth Rate")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 4: Enrollment Indexed To First Month

        Elements: first month equals 100; later values show relative growth.

        Why: indexed charts make growth easy to explain to nontechnical reviewers.
        """
    ),
    code(
        """
        explain(
            "Indexed Enrollment",
            "Y-axis = enrollment relative to first month, where 100 means baseline.",
            "A value of 110 would mean observed enrollment is 10% above the first month.",
        )
        fig = px.line(monthly, x="report_month", y="indexed_to_first_month", markers=True, title="4. National Enrollment Indexed to First Month")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 5: Suppressed Row Share By Month

        Elements: x-axis is month; y-axis is share of rows where CMS used `.` instead of a numeric value.

        Why: this explains why totals are called observed/lower-bound enrollment.
        """
    ),
    code(
        """
        explain(
            "Suppressed Row Share",
            "Line = share of source rows with CMS suppression; higher means more missing numeric values.",
            "If suppression is stable, trend comparisons are more defensible. If it changes sharply, caveats matter more.",
        )
        fig = px.line(quality_by_month, x="report_month_label", y="suppressed_row_share", markers=True, title="5. CMS Suppressed Enrollment Row Share")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 6: Numeric vs Suppressed Rows

        Elements: stacked bars split each month into numeric rows and suppressed rows.

        Why: shows actual raw-data usability before modeling.
        """
    ),
    code(
        """
        explain(
            "Numeric vs Suppressed Rows",
            "Stacked bars = source row composition; color separates numeric and suppressed enrollment rows.",
            "A stable composition means modeling comparisons are less likely to be distorted by missingness shifts.",
        )
        row_quality_long = quality_by_month.melt(
            id_vars=["report_month_label"],
            value_vars=["numeric_rows", "suppressed_rows"],
            var_name="row_type",
            value_name="row_count",
        )
        fig = px.bar(row_quality_long, x="report_month_label", y="row_count", color="row_type", title="6. Numeric vs Suppressed Rows by Month")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 7: Latest Enrollment By Plan Type

        Elements: x-axis is plan type; y-axis is latest observed enrollment.

        Why: identifies the largest plan categories driving the market.
        """
    ),
    code(
        """
        explain(
            "Latest Enrollment by Plan Type",
            "Bar height = latest observed enrollment in each plan type.",
            "Tall bars are the plan segments most important for the dashboard and forecast story.",
        )
        latest_plan = plan_monthly[plan_monthly["report_month"].eq(latest_month)].sort_values("observed_enrollment", ascending=False)
        fig = px.bar(latest_plan, x="plan_type", y="observed_enrollment", title=f"7. Latest Enrollment by Plan Type ({latest_label})")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 8: Plan-Type Enrollment Over Time

        Elements: x-axis is month; y-axis is enrollment; color is plan type.

        Why: reveals whether national growth comes from one segment or broad market movement.
        """
    ),
    code(
        """
        explain(
            "Plan-Type Enrollment Over Time",
            "Each colored line is one major plan type; slope shows segment growth or decline.",
            "Diverging lines indicate plan-mix shifts that should be mentioned in business interpretation.",
        )
        fig = px.line(
            plan_monthly[plan_monthly["plan_type"].isin(top_8_plan_types)],
            x="report_month",
            y="observed_enrollment",
            color="plan_type",
            markers=True,
            title="8. Major Plan-Type Enrollment Trends",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 9: Plan-Type National Share Over Time

        Elements: x-axis is month; y-axis is share of national observed enrollment; color is plan type.

        Why: a plan type can be growing in absolute terms but shrinking in share; this chart separates scale from mix.
        """
    ),
    code(
        """
        explain(
            "Plan-Type Share Over Time",
            "Y-axis = each plan type's share of national observed enrollment.",
            "Rising share means the segment is gaining importance relative to the rest of the market.",
        )
        fig = px.line(
            plan_monthly[plan_monthly["plan_type"].isin(top_8_plan_types)],
            x="report_month",
            y="national_share",
            color="plan_type",
            markers=True,
            title="9. Plan-Type Share of National Enrollment",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 10: Plan-Type Absolute Growth

        Elements: x-axis is plan type; y-axis is first-to-last absolute enrollment growth.

        Why: identifies which plan segments create the largest enrollment opportunity.
        """
    ),
    code(
        """
        explain(
            "Plan-Type Absolute Growth",
            "Bar height = latest enrollment minus first-month enrollment.",
            "Positive bars are expanding segments; negative bars are shrinking segments.",
        )
        fig = px.bar(first_last_plan.sort_values("absolute_growth", ascending=False), x="plan_type", y="absolute_growth", title="10. Plan-Type Absolute Growth")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 11: Latest Enrollment By State

        Elements: x-axis is state; y-axis is latest observed enrollment.

        Why: identifies large markets for RCM targeting and dashboard filtering.
        """
    ),
    code(
        """
        explain(
            "Latest Enrollment by State",
            "Bar height = latest observed MA enrollment by state.",
            "Large states may dominate national forecast movement and deserve separate model review.",
        )
        latest_state = state_monthly[state_monthly["report_month"].eq(latest_month)].sort_values("observed_enrollment", ascending=False)
        fig = px.bar(latest_state.head(25), x="state", y="observed_enrollment", title=f"11. Top States by Latest Enrollment ({latest_label})")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 12: Top-State Enrollment Trends

        Elements: x-axis is month; y-axis is enrollment; color is state.

        Why: checks whether large states move similarly or have different trajectories.
        """
    ),
    code(
        """
        explain(
            "Top-State Enrollment Trends",
            "Each colored line is a top state by absolute growth.",
            "Parallel upward slopes imply broad growth; crossing lines imply changing geographic opportunity.",
        )
        fig = px.line(
            state_monthly[state_monthly["state"].isin(top_10_states)],
            x="report_month",
            y="observed_enrollment",
            color="state",
            markers=True,
            title="12. Top-Growth State Enrollment Trends",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 13: State Absolute Growth

        Elements: x-axis is state; y-axis is first-to-last enrollment growth.

        Why: this is the simplest geography opportunity ranking.
        """
    ),
    code(
        """
        explain(
            "State Absolute Growth",
            "Bar height = enrollment gained or lost from first to latest month.",
            "Highest positive bars are strongest geographic opportunity candidates.",
        )
        fig = px.bar(state_growth.head(25), x="state", y="absolute_growth", title="13. Top States by Absolute Growth")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 14: State Growth Rate

        Elements: x-axis is state; y-axis is first-to-last percentage growth.

        Why: percentage growth highlights smaller but fast-growing states.
        """
    ),
    code(
        """
        explain(
            "State Growth Rate",
            "Bar height = percentage growth from first month to latest month.",
            "Use this with absolute growth, because tiny markets can have high percentages.",
        )
        state_growth_rate_plot = state_growth.sort_values("growth_pct", ascending=False).head(25)
        fig = px.bar(state_growth_rate_plot, x="state", y="growth_pct", title="14. Top States by Growth Rate")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 15: State Scale vs Growth

        Elements: x-axis is latest enrollment; y-axis is growth rate; marker size is absolute growth magnitude.

        Why: separates large stable markets from smaller fast-growing markets.
        """
    ),
    code(
        """
        explain(
            "State Scale vs Growth",
            "Right = larger current markets; higher = faster growth; bigger marker = larger absolute movement.",
            "Best sales targets often sit high and to the right, or high with enough scale to matter.",
        )
        state_growth_plot = state_growth.copy()
        state_growth_plot["abs_growth_for_marker"] = state_growth_plot["absolute_growth"].abs()
        fig = px.scatter(
            state_growth_plot,
            x="last_enrollment",
            y="growth_pct",
            size="abs_growth_for_marker",
            hover_name="state",
            title="15. State Scale vs Growth",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 16: State Volatility vs Growth

        Elements: x-axis is average monthly growth; y-axis is volatility of monthly growth; marker size is latest enrollment.

        Why: high growth with low volatility is easier to forecast; high volatility needs caution.
        """
    ),
    code(
        """
        explain(
            "State Volatility vs Growth",
            "X-axis = average monthly growth; y-axis = volatility; marker size = current market scale.",
            "Low volatility and positive growth are better candidates for reliable state-level forecasting.",
        )
        volatility_plot = state_growth.dropna(subset=["avg_mom_growth_pct", "volatility_mom_growth_pct"]).copy()
        volatility_plot["latest_size"] = volatility_plot["last_enrollment"].clip(lower=1)
        fig = px.scatter(
            volatility_plot,
            x="avg_mom_growth_pct",
            y="volatility_mom_growth_pct",
            size="latest_size",
            hover_name="state",
            title="16. State Volatility vs Average Monthly Growth",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 17: County Absolute Growth

        Elements: x-axis is county label; y-axis is first-to-last observed enrollment growth.

        Why: county-level opportunity is useful for maps and regional sales conversations.
        """
    ),
    code(
        """
        explain(
            "County Absolute Growth",
            "Bar height = observed enrollment growth at county/FIPS level.",
            "Top counties can become map highlights or target-market examples.",
        )
        county_growth_plot = county_growth.head(30).copy()
        county_growth_plot["county_label"] = county_growth_plot["county"] + ", " + county_growth_plot["state"]
        fig = px.bar(county_growth_plot, x="county_label", y="absolute_growth", title="17. Top Counties by Absolute Growth")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 18: County Growth Rate

        Elements: x-axis is county label; y-axis is growth rate.

        Why: highlights fast-growing local markets, but should be read with scale.
        """
    ),
    code(
        """
        explain(
            "County Growth Rate",
            "Bar height = percentage growth from first to latest month.",
            "High growth rates in low-volume counties need validation before being used as a headline.",
        )
        county_growth_rate_plot = county_growth.replace([np.inf, -np.inf], np.nan).dropna(subset=["growth_pct"]).sort_values("growth_pct", ascending=False).head(30).copy()
        county_growth_rate_plot["county_label"] = county_growth_rate_plot["county"] + ", " + county_growth_rate_plot["state"]
        fig = px.bar(county_growth_rate_plot, x="county_label", y="growth_pct", title="18. Top Counties by Growth Rate")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 19: County Scale vs Growth

        Elements: x-axis is latest county enrollment; y-axis is growth rate; marker size is absolute growth.

        Why: balances county scale against momentum.
        """
    ),
    code(
        """
        explain(
            "County Scale vs Growth",
            "Right = larger counties; higher = faster growth; marker size = absolute growth magnitude.",
            "Counties high and right are stronger candidates for opportunity-map emphasis.",
        )
        county_scatter = county_growth.replace([np.inf, -np.inf], np.nan).dropna(subset=["growth_pct"]).copy()
        county_scatter = county_scatter[county_scatter["last_enrollment"] > 0]
        county_scatter["abs_growth_for_marker"] = county_scatter["absolute_growth"].abs().clip(lower=1)
        county_scatter["county_label"] = county_scatter["county"] + ", " + county_scatter["state"]
        fig = px.scatter(
            county_scatter,
            x="last_enrollment",
            y="growth_pct",
            size="abs_growth_for_marker",
            hover_name="county_label",
            title="19. County Scale vs Growth",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 20: Missing/Suppressed Enrollment Reasons

        Elements: x-axis is missing reason; y-axis is row count.

        Why: documents how null-like values are handled.
        """
    ),
    code(
        """
        explain(
            "Missing/Suppressed Enrollment Reasons",
            "Bars show whether enrollment is numeric, CMS-suppressed, blank, or non-numeric.",
            "This proves missingness is handled explicitly rather than hidden by dropping rows.",
        )
        missing_reason_counts = ma["enrolled_missing_reason"].value_counts(dropna=False).rename_axis("reason").reset_index(name="rows")
        fig = px.bar(missing_reason_counts, x="reason", y="rows", title="20. Enrollment Missing/Suppression Reasons")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 21: Duplicate Business-Key Rows By Month

        Elements: x-axis is month; y-axis is number of rows involved in duplicate business keys.

        Why: helps decide whether aggregation is sufficient or whether source rows need manual review.
        """
    ),
    code(
        """
        explain(
            "Duplicate Rows by Month",
            "Bar height = rows whose month/state/county/FIPS/plan-type key appears more than once.",
            "If bars are zero or small, duplicate risk is low. If not, model tables should aggregate keys deliberately.",
        )
        duplicate_by_month = (
            ma.groupby("report_month_label", as_index=False)
            .agg(duplicate_rows=("is_duplicate_business_key", "sum"))
        )
        fig = px.bar(duplicate_by_month, x="report_month_label", y="duplicate_rows", title="21. Duplicate Business-Key Rows by Month")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 22: State Month-over-Month Outlier Counts

        Elements: x-axis is state; y-axis is number of IQR-flagged month-over-month changes.

        Why: identifies geographies that may need robust forecasting or manual review.
        """
    ),
    code(
        """
        explain(
            "State Outlier Counts",
            "Bar height = number of state monthly changes flagged by the IQR rule.",
            "States with many flags may be less stable forecast targets or need state-specific notes.",
        )
        state_outlier_counts = (
            state_outlier_flags.groupby("state", as_index=False)
            .agg(outlier_months=("mom_change_is_outlier_iqr", "sum"))
            .sort_values("outlier_months", ascending=False)
        )
        fig = px.bar(state_outlier_counts.head(25), x="state", y="outlier_months", title="22. State MoM Outlier Counts")
        fig.show()
        """
    ),
    md(
        """
        ### Graph 23: State Heatmap Of Enrollment

        Elements: x-axis is month; y-axis is state; color intensity is observed enrollment.

        Why: heatmaps make broad geographic scale patterns easy to scan.
        """
    ),
    code(
        """
        explain(
            "State Enrollment Heatmap",
            "Darker color = higher observed enrollment for that state/month.",
            "Persistent dark rows are large markets; color changes over time show movement.",
        )
        heatmap_states = latest_state.head(20)["state"].tolist()
        heatmap_data = state_monthly[state_monthly["state"].isin(heatmap_states)]
        fig = px.density_heatmap(
            heatmap_data,
            x="report_month_label",
            y="state",
            z="observed_enrollment",
            histfunc="sum",
            title="23. State Enrollment Heatmap - Top 20 Latest States",
        )
        fig.show()
        """
    ),
    md(
        """
        ### Graph 24: Plan-Type And State Mix For Latest Month

        Elements: treemap hierarchy is state then plan type; box size is latest observed enrollment.

        Why: shows which state/plan-type combinations dominate the current market.
        """
    ),
    code(
        """
        explain(
            "Latest State/Plan-Type Treemap",
            "Each rectangle area = latest observed enrollment; hierarchy = state then plan type.",
            "Large rectangles identify the most important geographic and plan-type segments.",
        )
        latest_state_plan = (
            ma[ma["report_month"].eq(latest_month)]
            .groupby(["state", "plan_type"], as_index=False)
            .agg(observed_enrollment=("enrolled", "sum"))
        )
        latest_state_plan = latest_state_plan[latest_state_plan["state"].isin(latest_state.head(12)["state"])]
        fig = px.treemap(
            latest_state_plan,
            path=["state", "plan_type"],
            values="observed_enrollment",
            title=f"24. Latest Enrollment Mix by State and Plan Type ({latest_label})",
        )
        fig.show()
        """
    ),
]


def main() -> None:
    notebook = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells = notebook["cells"]

    # Remove prior inserted sections if the script is rerun.
    filtered = []
    skip = False
    for cell in cells:
        source = "".join(cell.get("source", []))
        if source.startswith("## Missing, Duplicate, And Outlier Handling"):
            skip = True
        if source.startswith("## Forecasting Readiness Summary"):
            skip = False
        if not skip:
            filtered.append(cell)
    cells = filtered

    insert_at = next(
        i for i, cell in enumerate(cells)
        if "".join(cell.get("source", [])).startswith("## Forecasting Readiness Summary")
    )
    cells[insert_at:insert_at] = missing_duplicate_outlier_cells + visual_cells

    notebook["cells"] = cells
    NB_PATH.write_text(json.dumps(notebook, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
