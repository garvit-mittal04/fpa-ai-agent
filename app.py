import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary, get_rolling_trends
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_commentary, generate_risk_flags
from report_generator import generate_excel_report

st.set_page_config(
    page_title="FP&A AI Analyst Agent",
    page_icon="📊",
    layout="wide"
)

st.title("📊 FP&A AI Analyst Agent")
st.caption("Automated Variance Analysis & Management Commentary Generator")

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Upload Data")
    actuals_file = st.file_uploader("Upload Actuals CSV", type=["csv"])
    budget_file = st.file_uploader("Upload Budget CSV", type=["csv"])

    use_sample = st.checkbox("Use sample data instead", value=True)

    run_btn = st.button("▶ Run Analysis", use_container_width=True, type="primary")

# ── MAIN LOGIC ────────────────────────────────────────────
if run_btn:
    with st.spinner("Loading data into MySQL..."):
        if use_sample:
            actuals_path = os.path.join(BASE_DIR, "sample_data/actual.csv")
            budget_path = os.path.join(BASE_DIR, "sample_data/budget.csv")
        else:
            if not actuals_file or not budget_file:
                st.error("Please upload both Actuals and Budget CSV files.")
                st.stop()
            actuals_path = os.path.join(BASE_DIR, "sample_data/uploaded_actuals.csv")
            budget_path = os.path.join(BASE_DIR, "sample_data/uploaded_budget.csv")
            pd.read_csv(actuals_file).to_csv(actuals_path, index=False)
            pd.read_csv(budget_file).to_csv(budget_path, index=False)

        load_csv_to_db(actuals_path, budget_path)

    with st.spinner("Running variance analysis..."):
        variance_df = get_variance_analysis()
        dept_df = get_department_summary()
        trends_df = get_rolling_trends()
        variance_df = detect_anomalies(variance_df)
        anomaly_summary = get_anomaly_summary(variance_df)
        risk_flags = generate_risk_flags(variance_df)

    st.success("Analysis complete!")

    # ── KPI CARDS ─────────────────────────────────────────
    st.subheader("📌 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_variance = variance_df["variance_dollar"].sum()
    total_variance_pct = round((total_variance / total_budget) * 100, 2) if total_budget else 0

    col1.metric("Total Actual", f"${total_actual:,.0f}")
    col2.metric("Total Budget", f"${total_budget:,.0f}")
    col3.metric("Total Variance $", f"${total_variance:,.0f}", delta=f"{total_variance:,.0f}")
    col4.metric("Total Variance %", f"{total_variance_pct}%", delta=f"{total_variance_pct}%")

    st.divider()

    # ── DEPARTMENT SUMMARY TABLE ───────────────────────────
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
                for flag in risk_flags:
    st.warning(flag)
        else:
            st.success("No items exceed 10% variance threshold.")

    st.divider()

    # ── WATERFALL CHART ────────────────────────────────────
    st.subheader("📉 Variance Waterfall — Top 10 Line Items")
    top10 = variance_df.head(10).copy()
    colors = ["red" if v < 0 else "green" for v in top10["variance_dollar"]]

    fig_waterfall = go.Figure(go.Bar(
        x=top10["line_item"] + " (" + top10["period"] + ")",
        y=top10["variance_dollar"],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in top10["variance_dollar"]],
        textposition="outside"
    ))
    fig_waterfall.update_layout(
        xaxis_title="Line Item",
        yaxis_title="Variance ($)",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    # ── TREND CHART ────────────────────────────────────────
    st.subheader("📈 Actual vs Rolling 3-Month Average by Department")
    dept_filter = st.selectbox("Select Department", trends_df["department"].unique())
    filtered = trends_df[trends_df["department"] == dept_filter]

    fig_trend = go.Figure()
    for item in filtered["line_item"].unique():
        item_df = filtered[filtered["line_item"] == item].copy()
        item_df["period"] = item_df["period"].astype(str)
        fig_trend.add_trace(go.Scatter(
            x=item_df["period"],
            y=item_df["actual_amount"],
            mode="lines+markers",
            name=item
        ))
    fig_trend.update_layout(
        xaxis_title="Period",
        yaxis_title="Amount ($)",
        xaxis=dict(type="category"),
        height=400,
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── ANOMALIES ──────────────────────────────────────────
    st.subheader(f"🔍 AI-Detected Anomalies ({anomaly_summary['count']} found)")
    if anomaly_summary["count"] > 0:
        for a in anomaly_summary["items"]:
            st.error(f"**{a['period']}** | {a['department']} | {a['line_item']} | ${a['variance_dollar']:,.0f} ({a['variance_pct']}%)")
    else:
        st.success("No anomalies detected.")

    st.divider()

    # ── AI COMMENTARY ──────────────────────────────────────
    st.subheader("🤖 AI-Generated Management Commentary")
    with st.spinner("Generating commentary with AI..."):
        commentary = generate_commentary(variance_df, anomaly_summary, dept_df)

    st.text_area("Management Commentary (editable)", value=commentary, height=300)
    st.download_button(
        label="📋 Download Commentary",
        data=commentary,
        file_name="management_commentary.txt",
        mime="text/plain"
    )

    st.divider()

    # ── EXCEL EXPORT ───────────────────────────────────────
    st.subheader("📥 Download Report")
    excel_path = os.path.join(BASE_DIR, "outputs/variance_report.xlsx")

    generate_excel_report(variance_df, dept_df, anomaly_summary, commentary, excel_path)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="📊 Download Excel Variance Report",
            data=f,
            file_name="FPA_Variance_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    st.info("👈 Upload your data or use sample data, then click **Run Analysis** to start.")