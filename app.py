import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary, get_rolling_trends
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_commentary, generate_risk_flags
from report_generator import generate_excel_report

load_dotenv()

st.set_page_config(page_title="FP&A AI Agent", page_icon="📊", layout="wide")

st.markdown("""
<style>
/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #0d1117 100%);
    border-right: 1px solid #1e2d40;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label {
    color: #e2e8f0 !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #111827 0%, #1a2234 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: transform 0.2s ease;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f59e0b;
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.5px;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.9rem;
    font-weight: 600;
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Dataframes ── */
div[data-testid="stDataFrame"] {
    border: 1px solid #1e2d40;
    border-radius: 14px;
    overflow: hidden;
}

/* ── Buttons ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
    box-shadow: 0 4px 15px rgba(245,158,11,0.3) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 6px 20px rgba(245,158,11,0.5) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(245,158,11,0.25) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(245,158,11,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: #1a2234 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d3f55 !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #243048 !important;
    border-color: #3d5a80 !important;
}

/* ── Section headings ── */
h1 { color: #f1f5f9 !important; letter-spacing: -0.5px; }
h2, h3 { color: #e2e8f0 !important; }

/* ── Alerts ── */
.stAlert { border-radius: 12px !important; }

/* ── Text area ── */
.stTextArea textarea {
    background-color: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}

/* ── Selectbox / dropdowns ── */
.stSelectbox > div > div {
    background-color: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* ── Info box ── */
.info-box {
    background: linear-gradient(135deg, #0f2137, #132a45);
    border: 1px solid #1e3a5f;
    border-left: 4px solid #f59e0b;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #94a3b8;
    font-size: 0.88rem;
    line-height: 1.6;
}

/* ── Section card ── */
.section-card {
    background: linear-gradient(135deg, #0f1825, #111d2e);
    border: 1px solid #1e2d40;
    border-radius: 18px;
    padding: 24px;
    margin: 12px 0;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    background: #1a2e45;
    border: 1px solid #1e3a5f;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    color: #94a3b8;
    margin-right: 6px;
    letter-spacing: 0.05em;
}
.badge-gold {
    background: rgba(245,158,11,0.12);
    border-color: rgba(245,158,11,0.3);
    color: #f59e0b;
}

/* ── Divider ── */
hr {
    border: none;
    border-top: 1px solid #1e2d40 !important;
    margin: 28px 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 8px 0 20px 0;">
    <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:2.4rem;">📊</span>
        <div>
            <h1 style="margin:0; font-size:2rem; font-weight:800;
                background: linear-gradient(90deg, #f59e0b, #fbbf24, #f1f5f9);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                FP&A AI Analyst Agent
            </h1>
            <p style="margin:0; color:#64748b; font-size:0.9rem; letter-spacing:0.05em;">
                AUTOMATED VARIANCE ANALYSIS &amp; MANAGEMENT COMMENTARY
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 16px 0;">
        <span style="font-size:1.8rem;">📁</span>
        <p style="color:#94a3b8; font-size:0.8rem; margin:4px 0 0 0;
            text-transform:uppercase; letter-spacing:0.1em;">Data Input</p>
    </div>
    """, unsafe_allow_html=True)

    use_sample = st.button("⚡ Load Sample Data", use_container_width=True)
    st.divider()
    actual_file = st.file_uploader("Upload Actuals CSV", type=["csv"])
    budget_file = st.file_uploader("Upload Budget CSV", type=["csv"])

SAMPLE_ACTUAL = os.path.join(BASE_DIR, "sample_data", "actual.csv")
SAMPLE_BUDGET = os.path.join(BASE_DIR, "sample_data", "budget.csv")

if use_sample:
    st.session_state["actual_df"] = pd.read_csv(SAMPLE_ACTUAL)
    st.session_state["budget_df"] = pd.read_csv(SAMPLE_BUDGET)
    st.sidebar.success("✅ Sample data loaded!")

if actual_file and budget_file:
    st.session_state["actual_df"] = pd.read_csv(actual_file)
    st.session_state["budget_df"] = pd.read_csv(budget_file)
    st.sidebar.success("✅ Files uploaded!")

# ── PERIOD SELECTOR ────────────────────────────────────────────────────────────
if "actual_df" in st.session_state:
    with st.sidebar:
        st.divider()
        st.markdown("""
        <p style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase;
            letter-spacing:0.1em; margin-bottom:8px;">📅 Analysis Period</p>
        """, unsafe_allow_html=True)

        all_periods = sorted(st.session_state["actual_df"]["period"].unique().tolist())
        period_options = ["All Periods"] + all_periods

        selected_period = st.selectbox(
            "Select period",
            options=period_options,
            index=len(period_options) - 1,   # default to latest period
            label_visibility="collapsed"
        )

        if selected_period != "All Periods":
            st.markdown(f"""
            <div class="info-box">
                Analyzing <strong style="color:#f59e0b;">{selected_period}</strong> only.
                Switch to "All Periods" to run a full historical analysis.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-box">
                ⚠️ All periods selected. KPI totals will span the full dataset.
                For a monthly close report, select a single period.
            </div>
            """, unsafe_allow_html=True)

    st.session_state["selected_period"] = selected_period

with st.sidebar:
    st.divider()
    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

# ── MAIN ANALYSIS ──────────────────────────────────────────────────────────────
if run_btn:
    if "actual_df" not in st.session_state:
        st.warning("⚠️ Please upload data or load sample data first.")
        st.stop()

    actual_df = st.session_state["actual_df"].copy()
    budget_df = st.session_state["budget_df"].copy()
    selected_period = st.session_state.get("selected_period", "All Periods")

    # Filter to selected period if not "All Periods"
    if selected_period != "All Periods":
        actual_df = actual_df[actual_df["period"] == selected_period]
        budget_df = budget_df[budget_df["period"] == selected_period]

    with st.spinner("⚙️ Running analysis pipeline..."):
        load_csv_to_db(actual_df, budget_df)
        variance_df = get_variance_analysis()
        dept_df = get_department_summary()
        trends_df = get_rolling_trends()
        variance_df = detect_anomalies(variance_df)
        anomaly_summary = get_anomaly_summary(variance_df)
        risk_flags = generate_risk_flags(variance_df)

    # ── PERIOD BANNER ──────────────────────────────────────────────────────────
    period_label = selected_period if selected_period != "All Periods" else "Full Dataset"
    contamination_pct = anomaly_summary.get("contamination_used", 10.0)
    st.markdown(f"""
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px; align-items:center;">
        <span class="badge badge-gold">📅 {period_label}</span>
        <span class="badge">{len(variance_df):,} line items analyzed</span>
        <span class="badge">🎯 Sensitivity: {contamination_pct:.0f}%</span>
        <span class="badge">{anomaly_summary.get('total_anomalies', 0)} anomalies flagged</span>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ──────────────────────────────────────────────────────────────
    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Actual", f"${total_actual:,.0f}")
    k2.metric("📋 Total Budget", f"${total_budget:,.0f}")
    k3.metric("📊 Net Variance", f"${total_var:,.0f}", delta=f"{total_var_pct:+.2f}%")
    k4.metric("🔍 Anomalies Detected", anomaly_summary.get("total_anomalies", 0))

    st.divider()

    # ── DEPARTMENT SUMMARY + RISK FLAGS ────────────────────────────────────────
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.markdown("### 🏢 Department Summary")
        dept_display = dept_df.copy()
        dept_display.columns = ["Department", "Actual ($)", "Budget ($)", "Variance ($)", "Variance %"]
        dept_display["Actual ($)"] = dept_display["Actual ($)"].apply(lambda x: f"${x:,.0f}")
        dept_display["Budget ($)"] = dept_display["Budget ($)"].apply(lambda x: f"${x:,.0f}")
        dept_display["Variance ($)"] = dept_display["Variance ($)"].apply(lambda x: f"${x:,.0f}")
        dept_display["Variance %"] = dept_display["Variance %"].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(dept_display, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### ⚠️ Risk Flags")
        if risk_flags:
            for flag in risk_flags:
                st.warning(flag)
        else:
            st.success("✅ No items exceed 10% variance threshold.")

    st.divider()

    # ── WATERFALL CHART ────────────────────────────────────────────────────────
    st.markdown("### 📉 Variance Waterfall — Top 10 Line Items")
    top10 = variance_df.head(10).copy()
    colors = ["#ef4444" if v < 0 else "#22c55e" for v in top10["variance_dollar"]]
    fig_waterfall = go.Figure(go.Bar(
        x=top10["line_item"] + "<br><span style='font-size:10px'>(" + top10["period"] + ")</span>",
        y=top10["variance_dollar"],
        marker=dict(
            color=colors,
            line=dict(color="rgba(255,255,255,0.05)", width=1)
        ),
        text=[f"${v:,.0f}" for v in top10["variance_dollar"]],
        textposition="outside",
        textfont=dict(color="#f1f5f9", size=11)
    ))
    fig_waterfall.update_layout(
        xaxis_title="",
        yaxis_title="Variance ($)",
        height=420,
        xaxis_tickangle=-30,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,14,26,0.6)",
        font_color="#f1f5f9",
        margin=dict(t=20, b=20),
        yaxis=dict(gridcolor="#1e2d40", zerolinecolor="#2d3f55"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        bargap=0.35
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.divider()

    # ── TREND CHART ────────────────────────────────────────────────────────────
    st.markdown("### 📈 Rolling 3-Month Trend by Department")
    if not trends_df.empty:
        palette = ["#f59e0b", "#3b82f6", "#22c55e", "#a855f7",
                   "#ec4899", "#14b8a6", "#f97316", "#64748b", "#06b6d4", "#84cc16"]
        fig_trend = go.Figure()
        depts = trends_df["department"].unique()
        for i, dept in enumerate(depts):
            dept_data = trends_df[trends_df["department"] == dept]
            fig_trend.add_trace(go.Scatter(
                x=dept_data["period"],
                y=dept_data["rolling_3m_avg"],
                mode="lines+markers",
                name=dept,
                line=dict(color=palette[i % len(palette)], width=2),
                marker=dict(size=5)
            ))
        fig_trend.update_layout(
            xaxis_title="Period",
            yaxis_title="Rolling 3M Avg ($)",
            height=420,
            legend_title="Department",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(10,14,26,0.6)",
            font_color="#f1f5f9",
            margin=dict(t=20, b=20),
            yaxis=dict(gridcolor="#1e2d40", zerolinecolor="#2d3f55"),
            xaxis=dict(gridcolor="#1e2d40"),
            legend=dict(bgcolor="rgba(15,24,37,0.8)", bordercolor="#1e2d40", borderwidth=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── ANOMALIES ──────────────────────────────────────────────────────────────
    st.markdown("### 🔍 AI-Detected Anomalies")
    anomaly_df = variance_df[variance_df["is_anomaly"] == True].copy()

    if not anomaly_df.empty:
        st.markdown(f"""
        <div class="info-box">
            <strong style="color:#f59e0b;">{len(anomaly_df)}</strong> anomalies detected across
            <strong style="color:#f59e0b;">{anomaly_summary.get('total_anomalies', 0)}</strong> line items
            in <strong style="color:#f59e0b;">{len(anomaly_summary.get('departments_affected', []))}</strong> departments
            — sensitivity set to <strong style="color:#f59e0b;">{contamination_pct:.0f}%</strong> for this dataset size.
        </div>
        """, unsafe_allow_html=True)

        display_cols = ["department", "line_item", "period",
                        "actual_amount", "budget_amount", "variance_dollar", "variance_pct"]
        st.dataframe(
            anomaly_df[display_cols].head(500),
            use_container_width=True,
            hide_index=True
        )
        if len(anomaly_df) > 500:
            st.caption(f"Showing top 500 of {len(anomaly_df)} anomalies. Download the Excel report for the full list.")
    else:
        st.success("✅ No anomalies detected.")

    st.divider()

    # ── AI COMMENTARY ──────────────────────────────────────────────────────────
    st.markdown("### 🤖 AI-Generated Management Commentary")
    with st.spinner("✍️ Generating board-ready commentary..."):
        commentary = generate_commentary(variance_df, anomaly_summary, dept_df)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f1825, #111d2e);
        border: 1px solid #1e3a5f; border-left: 4px solid #f59e0b;
        border-radius: 14px; padding: 24px; line-height: 1.9;
        color: #cbd5e1; font-size: 0.95rem; white-space: pre-wrap;">
{commentary}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── EXCEL EXPORT ───────────────────────────────────────────────────────────
    st.markdown("### 📥 Export Report")
    excel_path = os.path.join(BASE_DIR, "outputs", "variance_report.xlsx")
    os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
    generate_excel_report(variance_df, dept_df, commentary, excel_path)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Excel Report",
            data=f,
            file_name=f"variance_report_{period_label.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown(f"""
    <div class="info-box" style="margin-top:12px;">
        Report covers <strong style="color:#f59e0b;">{period_label}</strong> ·
        {len(variance_df):,} line items · {anomaly_summary.get('total_anomalies', 0)} anomalies ·
        3 sheets: Executive Summary, Variance Detail, AI Commentary
    </div>
    """, unsafe_allow_html=True)
