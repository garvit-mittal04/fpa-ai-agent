import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.sql_engine import (
    load_csv_to_db,
    get_variance_analysis,
    get_department_summary,
    get_rolling_trends,
)
from src.anomaly_detector import detect_anomalies, get_anomaly_summary
from src.commentary_agent import generate_risk_flags, generate_commentary


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="FP&A AI Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 FP&A AI Agent")
st.caption("Automate variance analysis, anomaly detection, risk flags, and management commentary.")


# -----------------------------
# PATHS
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_ACTUAL = BASE_DIR / "sample_data" / "actual.csv"
SAMPLE_BUDGET = BASE_DIR / "sample_data" / "budget.csv"


# -----------------------------
# HELPERS
# -----------------------------
def build_excel_report(
    variance_df: pd.DataFrame,
    dept_df: pd.DataFrame,
    trends_df: pd.DataFrame,
    anomaly_summary: dict,
    risk_flags: list,
    commentary: str,
) -> bytes:
    """
    Creates an in-memory Excel report and returns bytes.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        variance_df.to_excel(writer, sheet_name="Variance Analysis", index=False)
        dept_df.to_excel(writer, sheet_name="Department Summary", index=False)
        trends_df.to_excel(writer, sheet_name="Rolling Trends", index=False)

        anomaly_rows = anomaly_summary.get("top_anomalies", [])
        anomaly_df = pd.DataFrame(anomaly_rows) if anomaly_rows else pd.DataFrame(
            columns=["period", "department", "line_item", "variance_dollar", "variance_pct"]
        )
        anomaly_df.to_excel(writer, sheet_name="Top Anomalies", index=False)

        risk_df = pd.DataFrame({"risk_flag": risk_flags if risk_flags else ["No risk flags available"]})
        risk_df.to_excel(writer, sheet_name="Risk Flags", index=False)

        commentary_df = pd.DataFrame({"management_commentary": [commentary]})
        commentary_df.to_excel(writer, sheet_name="Commentary", index=False)

    output.seek(0)
    return output.getvalue()


def safe_format_currency(value):
    try:
        return f"${value:,.0f}"
    except Exception:
        return str(value)


def safe_format_pct(value):
    try:
        return f"{value:+.1f}%"
    except Exception:
        return str(value)


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Data Input")

use_sample = st.sidebar.button("Load Sample Data", type="primary", width="stretch")

actual_file = st.sidebar.file_uploader("Upload Actuals CSV", type=["csv"])
budget_file = st.sidebar.file_uploader("Upload Budget CSV", type=["csv"])

run_btn = st.sidebar.button("▶ Run Analysis", width="stretch")

st.sidebar.markdown("---")
st.sidebar.caption("Use sample data for quick testing.")


# -----------------------------
# LOAD DATA INTO SESSION STATE
# -----------------------------
if use_sample:
    actual_df = pd.read_csv(SAMPLE_ACTUAL)
    budget_df = pd.read_csv(SAMPLE_BUDGET)
    st.session_state["actual_df"] = actual_df
    st.session_state["budget_df"] = budget_df
    st.sidebar.success("Sample data loaded.")

if actual_file is not None and budget_file is not None:
    st.session_state["actual_df"] = pd.read_csv(actual_file)
    st.session_state["budget_df"] = pd.read_csv(budget_file)
    st.sidebar.success("Uploaded files loaded.")


# -----------------------------
# PREVIEW
# -----------------------------
if "actual_df" in st.session_state and "budget_df" in st.session_state:
    with st.expander("Preview Loaded Data"):
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Actuals")
            st.dataframe(st.session_state["actual_df"].head(10), width="stretch")

        with c2:
            st.subheader("Budget")
            st.dataframe(st.session_state["budget_df"].head(10), width="stretch")


# -----------------------------
# RUN ANALYSIS
# -----------------------------
if run_btn:
    if "actual_df" not in st.session_state or "budget_df" not in st.session_state:
        st.warning("Please upload data or load sample data first.")
        st.stop()

    actual_df = st.session_state["actual_df"]
    budget_df = st.session_state["budget_df"]

    with st.spinner("Running analysis..."):
        load_csv_to_db(actual_df, budget_df)

        variance_df = get_variance_analysis()
        dept_df = get_department_summary()
        trends_df = get_rolling_trends()

        variance_df = detect_anomalies(variance_df)
        anomaly_summary = get_anomaly_summary(variance_df)

        try:
            risk_flags = generate_risk_flags(variance_df)
        except Exception as e:
            risk_flags = [f"Risk flag generation failed: {str(e)}"]

        try:
            commentary = generate_commentary(variance_df, anomaly_summary, dept_df)
        except Exception as e:
            commentary = f"Management commentary generation failed: {str(e)}"

    st.success("Analysis complete.")

    # -----------------------------
    # KPI CARDS
    # -----------------------------
    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Actual", safe_format_currency(total_actual))
    k2.metric("Total Budget", safe_format_currency(total_budget))
    k3.metric("Net Variance", safe_format_currency(total_var), safe_format_pct(total_var_pct))
    k4.metric(
        "Anomalies Detected",
        anomaly_summary.get("total_anomalies", 0),
        f"{anomaly_summary.get('anomaly_rate', 0):.1f}% of records",
    )

    st.divider()

    # -----------------------------
    # CHARTS
    # -----------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Budget vs Actual by Department")

        if not dept_df.empty:
            dept_plot = dept_df.copy()

            fig_dept = go.Figure()
            fig_dept.add_trace(
                go.Bar(
                    x=dept_plot["department"],
                    y=dept_plot["total_budget"],
                    name="Budget",
                )
            )
            fig_dept.add_trace(
                go.Bar(
                    x=dept_plot["department"],
                    y=dept_plot["total_actual"],
                    name="Actual",
                )
            )
            fig_dept.update_layout(
                barmode="group",
                xaxis_title="Department",
                yaxis_title="Amount",
                height=420,
            )
            st.plotly_chart(fig_dept, width="stretch")
        else:
            st.info("No department summary available.")

    with c2:
        st.subheader("Top Variance Line Items")

        if not variance_df.empty:
            top_var = variance_df.copy()
            top_var["abs_variance"] = top_var["variance_dollar"].abs()
            top_var = top_var.sort_values("abs_variance", ascending=False).head(10)

            fig_var = px.bar(
                top_var,
                x="variance_dollar",
                y="line_item",
                color="department",
                orientation="h",
                height=420,
            )
            fig_var.update_layout(yaxis_title="", xaxis_title="Variance Dollar")
            st.plotly_chart(fig_var, width="stretch")
        else:
            st.info("No variance data available.")

    st.divider()

    # -----------------------------
    # TREND CHART
    # -----------------------------
    st.subheader("Rolling Budget vs Actual Trend")

    if not trends_df.empty:
        trend_plot = trends_df.copy()

        # Convert period safely if possible
        if "period" in trend_plot.columns:
            try:
                trend_plot["period"] = pd.to_datetime(trend_plot["period"])
            except Exception:
                pass

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=trend_plot["period"],
                y=trend_plot["budget_amount"],
                mode="lines+markers",
                name="Budget",
            )
        )
        fig_trend.add_trace(
            go.Scatter(
                x=trend_plot["period"],
                y=trend_plot["actual_amount"],
                mode="lines+markers",
                name="Actual",
            )
        )
        fig_trend.update_layout(height=420, xaxis_title="Period", yaxis_title="Amount")
        st.plotly_chart(fig_trend, width="stretch")
    else:
        st.info("No trend data available.")

    st.divider()

    # -----------------------------
    # TABS
    # -----------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Variance Analysis",
            "Department Summary",
            "Anomalies",
            "Risk Flags",
            "Management Commentary",
        ]
    )

    with tab1:
        st.subheader("Variance Analysis")
        display_variance = variance_df.copy()
        if "anomaly_score" in display_variance.columns:
            display_variance["is_anomaly"] = display_variance["is_anomaly"].map({True: "Yes", False: "No"})
        st.dataframe(display_variance, width="stretch")

    with tab2:
        st.subheader("Department Summary")
        st.dataframe(dept_df, width="stretch")

    with tab3:
        st.subheader("Top Anomalies")

        top_anomalies = anomaly_summary.get("top_anomalies", [])
        if top_anomalies:
            st.dataframe(pd.DataFrame(top_anomalies), width="stretch")
        else:
            st.info("No anomalies found.")

        st.markdown(
            f"""
**Departments affected:** {", ".join(anomaly_summary.get("departments_affected", [])) if anomaly_summary.get("departments_affected") else "None"}  
**Anomaly rate:** {anomaly_summary.get("anomaly_rate", 0):.2f}%
"""
        )

    with tab4:
        st.subheader("Risk Flags")
        if risk_flags:
            for flag in risk_flags:
                st.warning(flag)
        else:
            st.info("No risk flags generated.")

    with tab5:
        st.subheader("Management Commentary")
        st.write(commentary)

    st.divider()

    # -----------------------------
    # DOWNLOAD REPORT
    # -----------------------------
    report_bytes = build_excel_report(
        variance_df=variance_df,
        dept_df=dept_df,
        trends_df=trends_df,
        anomaly_summary=anomaly_summary,
        risk_flags=risk_flags,
        commentary=commentary,
    )

    st.download_button(
        label="⬇ Download Excel Report",
        data=report_bytes,
        file_name="variance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )