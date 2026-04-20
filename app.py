import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary, get_rolling_trends, validate_schema
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_commentary, generate_risk_flags
from report_generator import generate_excel_report

load_dotenv()

st.set_page_config(page_title="FP&A AI Agent", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #1f2937;
}
[data-testid="metric-container"] {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 16px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f59e0b;
    font-size: 1.8rem;
    font-weight: 700;
}
[data-testid="metric-container"] label { color: #9ca3af; }
div[data-testid="stDataFrame"] {
    border: 1px solid #1f2937;
    border-radius: 12px;
}
.stDownloadButton > button {
    background-color: #f59e0b !important;
    color: #000 !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: none !important;
}
.stButton > button[kind="primary"] {
    background-color: #f59e0b !important;
    color: #000 !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: none !important;
}
h1, h2, h3 { color: #f1f5f9 !important; }
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

st.title("📊 FP&A AI Analyst Agent")
st.caption("Automated Variance Analysis & Management Commentary Generator")

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Data Input")
    use_sample = st.button("Load Sample Data", use_container_width=True)
    st.divider()
    actual_file = st.file_uploader("Upload Actuals CSV", type=["csv"])
    budget_file = st.file_uploader("Upload Budget CSV", type=["csv"])
    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

SAMPLE_ACTUAL = os.path.join(BASE_DIR, "sample_data", "actual.csv")
SAMPLE_BUDGET = os.path.join(BASE_DIR, "sample_data", "budget.csv")

if use_sample:
    st.session_state["actual_df"] = pd.read_csv(SAMPLE_ACTUAL)
    st.session_state["budget_df"] = pd.read_csv(SAMPLE_BUDGET)
    st.sidebar.success("Sample data loaded!")

if actual_file and budget_file:
    actual_df = pd.read_csv(actual_file)
    budget_df = pd.read_csv(budget_file)

    # ── Input validation ───────────────────────────────────────────────────────
    try:
        validate_schema(actual_df, "Actuals")
        validate_schema(budget_df, "Budget")
        st.session_state["actual_df"] = actual_df
        st.session_state["budget_df"] = budget_df
        st.sidebar.success("Files validated and loaded!")
    except ValueError as e:
        st.sidebar.error(f"❌ Invalid file: {e}")

if run_btn:
    if "actual_df" not in st.session_state:
        st.warning("Please upload data or load sample data first.")
        st.stop()

    actual_df = st.session_state["actual_df"]
    budget_df = st.session_state["budget_df"]

    with st.spinner("Running analysis..."):
        try:
            load_csv_to_db(actual_df, budget_df)
        except ValueError as e:
            st.error(f"❌ Data loading failed: {e}")
            st.stop()

        variance_df    = get_variance_analysis()
        dept_df        = get_department_summary()
        trends_df      = get_rolling_trends()
        variance_df    = detect_anomalies(variance_df)
        anomaly_summary = get_anomaly_summary(variance_df)
        risk_flags     = generate_risk_flags(variance_df)

    st.divider()

    # ── KPI CARDS ──────────────────────────────────────────────────────────────
    total_actual  = variance_df["actual_amount"].sum()
    total_budget  = variance_df["budget_amount"].sum()
    total_var     = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Actual",       f"${total_actual:,.0f}")
    k2.metric("Total Budget",       f"${total_budget:,.0f}")
    k3.metric("Net Variance $",     f"${total_var:,.0f}", delta=f"{total_var_pct:+.2f}%")
    k4.metric("Anomalies Detected", anomaly_summary["total_anomalies"])

    st.divider()

    # ── DEPARTMENT SUMMARY + RISK FLAGS ────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🏢 Department Summary")
        dept_display = dept_df.copy()
        dept_display.columns = ["Department", "Actual", "Budget", "Variance $", "Variance %"]
        st.dataframe(dept_display, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("⚠️ Risk Flags")
        if risk_flags:
            for flag in risk_flags:
                st.warning(flag)
        else:
            st.success("No items exceed 10% variance threshold.")

    st.divider()

    # ── WATERFALL CHART ────────────────────────────────────────────────────────
    st.subheader("📉 Variance Waterfall — Top 10 Line Items")
    top10  = variance_df.head(10).copy()
    colors = ["red" if v < 0 else "green" for v in top10["variance_dollar"]]

    fig_waterfall = go.Figure(go.Bar(
        x=top10["line_item"] + " (" + top10["period"] + ")",
        y=top10["variance_dollar"],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in top10["variance_dollar"]],
        textposition="outside",
    ))
    fig_waterfall.update_layout(
        xaxis_title="Line Item", yaxis_title="Variance ($)",
        height=400, xaxis_tickangle=-45,
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a", font_color="#f1f5f9",
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.divider()

    # ── TREND CHART ────────────────────────────────────────────────────────────
    st.subheader("📈 Rolling 3-Month Trend by Department")
    if not trends_df.empty:
        fig_trend = go.Figure()
        for dept in trends_df["department"].unique():
            d = trends_df[trends_df["department"] == dept]
            fig_trend.add_trace(go.Scatter(
                x=d["period"], y=d["rolling_3m_avg"],
                mode="lines+markers", name=dept,
            ))
        fig_trend.update_layout(
            xaxis_title="Period", yaxis_title="Rolling 3M Avg ($)",
            height=400, legend_title="Department",
            paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a", font_color="#f1f5f9",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── ANOMALIES ──────────────────────────────────────────────────────────────
    st.subheader("🔍 AI-Detected Anomalies")
    anomaly_df = variance_df[variance_df["is_anomaly"] == True].copy()
    if not anomaly_df.empty:
        st.dataframe(
            anomaly_df[[
                "department", "line_item", "period",
                "actual_amount", "budget_amount",
                "variance_dollar", "variance_pct",
            ]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No anomalies detected.")

    st.divider()

    # ── AI COMMENTARY ──────────────────────────────────────────────────────────
    st.subheader("🤖 AI-Generated Management Commentary")
    with st.spinner("Generating commentary..."):
        commentary = generate_commentary(variance_df, anomaly_summary, dept_df)
    st.text_area("Management Commentary", value=commentary, height=300)

    st.divider()

    # ── EXCEL EXPORT ───────────────────────────────────────────────────────────
    st.subheader("📥 Export Report")
    excel_path = os.path.join(BASE_DIR, "outputs", "variance_report.xlsx")
    os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
    generate_excel_report(variance_df, dept_df, commentary, excel_path)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Excel Report",
            data=f,
            file_name="variance_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )