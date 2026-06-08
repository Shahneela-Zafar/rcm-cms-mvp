from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import PROCESSED_DIR, TABLE_DIR


st.set_page_config(page_title="CMS RCM MVP", layout="wide")


@st.cache_data
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "forecast": pd.read_csv(PROCESSED_DIR / "forecast_results.csv", parse_dates=["ds"]),
        "forecast_metrics": pd.read_csv(TABLE_DIR / "forecast_metrics.csv"),
        "state_growth": pd.read_csv(TABLE_DIR / "ma_scp_state_growth.csv"),
        "pa": pd.read_csv(PROCESSED_DIR / "pa_predictions.csv"),
        "delay": pd.read_csv(PROCESSED_DIR / "delay_predictions.csv"),
        "validation": pd.read_csv(TABLE_DIR / "model_validation_summary.csv"),
    }


data = load_data()

st.title("CMS RCM Revenue Opportunity & Prior Authorization Intelligence")
st.caption("Public CMS-data MVP. Revenue is a transparent enrollment-based proxy, not actual collections.")

forecast = data["forecast"]
metrics = data["forecast_metrics"]
best_rows = metrics.sort_values(["target", "mape"]).groupby("target").head(1)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Best enrollment model", best_rows[best_rows["target"].eq("observed_enrollment")]["model"].iloc[0])
col2.metric("Enrollment MAPE", f"{best_rows[best_rows['target'].eq('observed_enrollment')]['mape'].iloc[0]:.3%}")
col3.metric("PA demo accuracy", f"{pd.read_csv(TABLE_DIR / 'pa_model_metrics.csv')['accuracy'].iloc[0]:.1%}")
col4.metric("Delay high-risk combos", int(data["delay"]["delay_flag"].sum()))

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Forecast", "Growth Map", "Prior Auth", "Delay Risk", "Validation"])

with tab1:
    target = st.selectbox("Forecast target", ["observed_enrollment", "proxy_revenue"])
    model = st.selectbox("Model", sorted(forecast[forecast["target"].eq(target)]["model"].unique()))
    chart = forecast[(forecast["target"].eq(target)) & (forecast["model"].eq(model))]
    fig = px.line(chart, x="ds", y="yhat", color="period_type", title=f"{model} forecast: {target}")
    if chart["actual"].notna().any():
        fig.add_scatter(x=chart["ds"], y=chart["actual"], mode="markers+lines", name="actual")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(metrics[metrics["target"].eq(target)].sort_values("mape"), use_container_width=True)

with tab2:
    state_growth = data["state_growth"].copy()
    fig = px.scatter(
        state_growth,
        x="last_enrollment",
        y="growth_pct",
        size=state_growth["absolute_growth"].abs().clip(lower=1),
        hover_name="state",
        title="State scale vs growth",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(state_growth.head(25), use_container_width=True)

with tab3:
    pa = data["pa"]
    fig = px.histogram(pa, x="hybrid_denial_risk", color="hybrid_risk_bucket", title="PA hybrid denial-risk distribution")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pa.sort_values("hybrid_denial_risk", ascending=False).head(30), use_container_width=True)

with tab4:
    delay = data["delay"]
    fig = px.bar(
        delay.sort_values("delay_risk_score", ascending=False),
        x="procedure_type",
        y="delay_risk_score",
        color="payer_type",
        facet_col="is_expedited",
        title="Delay risk by procedure, payer, and urgency",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(delay.sort_values("delay_risk_score", ascending=False), use_container_width=True)

with tab5:
    st.dataframe(data["validation"], use_container_width=True)
    st.info("Outliers and CMS-suppressed rows are flagged rather than dropped. This keeps the public-data MVP honest and traceable.")

