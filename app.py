import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from sql_engine import (
    load_csv_to_db,
    get_variance_analysis,
    get_department_summary,
    get_rolling_trends,
)
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_commentary, generate_risk_flags
from report_generator import generate_excel_report

load_dotenv()

st.set_page_config(page_title="FP&A AI Agent", page_icon="📊", layout="wide")

# =========================
# STATE MANAGEMENT
# =========================

def clear_analysis():
    for k in [
        "analysis_done",
        "variance_df",
        "dept_df",
        "trends_df",
        "anomaly_summary",
        "risk_flags",
        "commentary",
        "data_signature",
    ]:
        st.session_state.pop(k, None)


def file_signature(f):
    if f is None:
        return None
    return (f.name, f.size)


# =========================
# HEADER
# =========================

st.title("📊 FP&A AI Analyst Agent")
st.caption("Automated Variance Analysis & Management Commentary")

# =========================
# SIDEBAR INPUT
# =========================

with st.sidebar:
    st.header("📁 Data Input")

    actual_file = st.file_uploader("Upload Actuals CSV", type=["csv"])
    budget_file = st.file_uploader("Upload Budget CSV", type=["csv"])

    run_btn = st.button("▶ Run Analysis")

# =========================
# CLEAR WHEN FILES REMOVED
# =========================

if actual_file is None or budget_file is None:
    clear_analysis()

# =========================
# LOAD DATA
# =========================

if actual_file and budget_file:
    current_sig = (file_signature(actual_file), file_signature(budget_file))

    if st.session_state.get("data_signature") != current_sig:
        st.session_state["actual_df"] = pd.read_csv(actual_file)
        st.session_state["budget_df"] = pd.read_csv(budget_file)
        st.session_state["data_signature"] = current_sig
        clear_analysis()

# =========================
# RUN ANALYSIS
# =========================

if run_btn:
    if "actual_df" not in st.session_state:
        st.warning("Upload files first")
        st.stop()

    with st.spinner("Running analysis..."):
        load_csv_to_db(st.session_state["actual_df"], st.session_state["budget_df"])

        variance_df = get_variance_analysis()
        dept_df = get_department_summary()
        trends_df = get_rolling_trends()

        variance_df = detect_anomalies(variance_df)
        anomaly_summary = get_anomaly_summary(variance_df)
        risk_flags = generate_risk_flags(variance_df)

        commentary = generate_commentary(variance_df, anomaly_summary, dept_df)

    st.session_state.update({
        "analysis_done": True,
        "variance_df": variance_df,
        "dept_df": dept_df,
        "trends_df": trends_df,
        "anomaly_summary": anomaly_summary,
        "risk_flags": risk_flags,
        "commentary": commentary,
    })

# =========================
# DISPLAY
# =========================

if st.session_state.get("analysis_done"):

    variance_df = st.session_state["variance_df"]
    dept_df = st.session_state["dept_df"]
    trends_df = st.session_state["trends_df"]
    anomaly_summary = st.session_state["anomaly_summary"]
    risk_flags = st.session_state["risk_flags"]
    commentary = st.session_state["commentary"]

    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Actual", f"${total_actual:,.0f}")
    col2.metric("Total Budget", f"${total_budget:,.0f}")
    col3.metric("Net Variance", f"${total_var:,.0f}", f"{total_var_pct:+.2f}%")
    col4.metric("Anomalies", anomaly_summary.get("total_anomalies", 0))

    # =========================
    # SYSTEM INSIGHT
    # =========================

    if anomaly_summary["total_anomalies"] > 0:
        st.error(f"🔴 {anomaly_summary['total_anomalies']} anomalies detected")
    else:
        st.success("🟢 Dataset stable")

    # =========================
    # DEPARTMENT TABLE
    # =========================

    st.subheader("Department Summary")
    st.dataframe(dept_df, use_container_width=True)

    # =========================
    # RISK FLAGS
    # =========================

    st.subheader("⚠️ Risk Flags")
    if risk_flags:
        for i, r in enumerate(risk_flags, 1):
            st.warning(f"{i}. {r}")
    else:
        st.success("No major risks")

    # =========================
    # WATERFALL
    # =========================

    st.subheader("📉 Variance Waterfall")

    top10 = variance_df.head(10)

    fig = go.Figure(
        go.Bar(
            x=top10["line_item"],
            y=top10["variance_dollar"],
            marker_color=["green" if v > 0 else "red" for v in top10["variance_dollar"]],
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # TREND
    # =========================

    st.subheader("📈 Rolling Trend")

    fig2 = go.Figure()

    for dept in trends_df["department"].unique():
        d = trends_df[trends_df["department"] == dept]
        fig2.add_trace(go.Scatter(x=d["period"], y=d["rolling_3m_avg"], name=dept))

    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # ANOMALIES
    # =========================

    st.subheader("🔍 Anomalies")

    anomaly_df = variance_df[variance_df["is_anomaly"] == True]

    if not anomaly_df.empty:
        st.dataframe(anomaly_df)
    else:
        st.success("No anomalies")

    # =========================
    # COMMENTARY
    # =========================

    st.subheader("🤖 Management Commentary")

    st.text_area("", commentary, height=250)

    st.download_button(
        "Download Commentary",
        commentary,
        file_name="commentary.txt"
    )

    # =========================
    # RAW DATA
    # =========================

    if st.checkbox("Show Raw Data"):
        st.dataframe(variance_df)

    # =========================
    # EXPORT
    # =========================

    st.subheader("📥 Export")

    output_path = os.path.join(BASE_DIR, "outputs", "report.xlsx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    generate_excel_report(variance_df, dept_df, commentary, output_path)

    with open(output_path, "rb") as f:
        st.download_button("Download Excel Report", f)
