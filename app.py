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

st.markdown(
    """
<style>
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

div[data-testid="stDataFrame"] {
    border: 1px solid #1e2d40;
    border-radius: 14px;
    overflow: hidden;
}

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

h1 {
    color: #f1f5f9 !important;
    letter-spacing: -0.5px;
}

h2, h3 {
    color: #e2e8f0 !important;
}

.stAlert {
    border-radius: 12px !important;
}

.stTextArea textarea {
    background-color: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}

.stSelectbox > div > div {
    background-color: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

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

hr {
    border: none;
    border-top: 1px solid #1e2d40 !important;
    margin: 28px 0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def run_pipeline(actual_df: pd.DataFrame, budget_df: pd.DataFrame):
    load_csv_to_db(actual_df, budget_df)
    variance_df = get_variance_analysis()
    dept_df = get_department_summary()
    trends_df = get_rolling_trends()
    variance_df = detect_anomalies(variance_df)
    anomaly_summary = get_anomaly_summary(variance_df)
    risk_flags = generate_risk_flags(variance_df)
    return variance_df, dept_df, trends_df, anomaly_summary, risk_flags


def _data_quality_messages(actual_df: pd.DataFrame, budget_df: pd.DataFrame):
    messages = []
    if actual_df.isnull().sum().sum() > 0:
        messages.append("Actuals file contains missing values.")
    if budget_df.isnull().sum().sum() > 0:
        messages.append("Budget file contains missing values.")
    if len(actual_df) == 0:
        messages.append("Actuals file has no rows.")
    if len(budget_df) == 0:
        messages.append("Budget file has no rows.")
    return messages


def _clear_analysis_state():
    keys_to_clear = [
        "analysis_ran",
        "variance_df",
        "dept_df",
        "trends_df",
        "anomaly_summary",
        "risk_flags",
        "period_label",
        "dq_messages",
        "commentary",
        "commentary_signature",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def _uploaded_file_signature(file):
    if file is None:
        return ("", 0)
    return (file.name, file.size)


st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
    <div style="text-align:center; padding: 8px 0 16px 0;">
        <span style="font-size:1.8rem;">📁</span>
        <p style="color:#94a3b8; font-size:0.8rem; margin:4px 0 0 0;
            text-transform:uppercase; letter-spacing:0.1em;">Data Input</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    use_sample = st.button("⚡ Load Sample Data", use_container_width=True)
    st.divider()
    actual_file = st.file_uploader("Upload Actuals CSV", type=["csv"])
    budget_file = st.file_uploader("Upload Budget CSV", type=["csv"])

SAMPLE_ACTUAL = os.path.join(BASE_DIR, "sample_data", "actual.csv")
SAMPLE_BUDGET = os.path.join(BASE_DIR, "sample_data", "budget.csv")

if use_sample:
    sample_sig = ("sample_actual.csv", "sample_budget.csv")
    if st.session_state.get("data_signature") != sample_sig:
        st.session_state["actual_df"] = pd.read_csv(SAMPLE_ACTUAL)
        st.session_state["budget_df"] = pd.read_csv(SAMPLE_BUDGET)
        st.session_state["data_signature"] = sample_sig
        _clear_analysis_state()
    st.sidebar.success("✅ Sample data loaded!")

if actual_file and budget_file:
    upload_sig = (_uploaded_file_signature(actual_file), _uploaded_file_signature(budget_file))
    if st.session_state.get("data_signature") != upload_sig:
        st.session_state["actual_df"] = pd.read_csv(actual_file)
        st.session_state["budget_df"] = pd.read_csv(budget_file)
        st.session_state["data_signature"] = upload_sig
        _clear_analysis_state()
    st.sidebar.success("✅ Files uploaded!")

if "actual_df" in st.session_state:
    with st.sidebar:
        st.divider()
        st.markdown(
            """
        <p style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase;
            letter-spacing:0.1em; margin-bottom:8px;">📅 Analysis Period</p>
        """,
            unsafe_allow_html=True,
        )

        all_periods = sorted(st.session_state["actual_df"]["period"].astype(str).unique().tolist())
        period_options = ["All Periods"] + all_periods

        default_index = len(period_options) - 1
        if "selected_period" in st.session_state and st.session_state["selected_period"] in period_options:
            default_index = period_options.index(st.session_state["selected_period"])

        selected_period = st.selectbox(
            "Select period",
            options=period_options,
            index=default_index,
            label_visibility="collapsed",
        )

        if selected_period != "All Periods":
            st.markdown(
                f"""
            <div class="info-box">
                Analyzing <strong style="color:#f59e0b;">{selected_period}</strong> only.
                Switch to "All Periods" to run a full historical analysis.
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class="info-box">
                ⚠️ All periods selected. KPI totals will span the full dataset.
                For a monthly close report, select a single period.
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.session_state["selected_period"] = selected_period

with st.sidebar:
    st.divider()
    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

if run_btn:
    if "actual_df" not in st.session_state:
        st.warning("⚠️ Please upload data or load sample data first.")
        st.stop()

    actual_df = st.session_state["actual_df"].copy()
    budget_df = st.session_state["budget_df"].copy()
    selected_period = st.session_state.get("selected_period", "All Periods")

    dq_messages = _data_quality_messages(actual_df, budget_df)

    if selected_period != "All Periods":
        actual_df = actual_df[actual_df["period"].astype(str) == selected_period]
        budget_df = budget_df[budget_df["period"].astype(str) == selected_period]

    with st.spinner("⚙️ Running analysis pipeline..."):
        variance_df, dept_df, trends_df, anomaly_summary, risk_flags = run_pipeline(
            actual_df, budget_df
        )

    st.session_state["analysis_ran"] = True
    st.session_state["variance_df"] = variance_df
    st.session_state["dept_df"] = dept_df
    st.session_state["trends_df"] = trends_df
    st.session_state["anomaly_summary"] = anomaly_summary
    st.session_state["risk_flags"] = risk_flags
    st.session_state["period_label"] = (
        selected_period if selected_period != "All Periods" else "Full Dataset"
    )
    st.session_state["dq_messages"] = dq_messages

    signature = (
        st.session_state["period_label"],
        len(variance_df),
        round(float(variance_df["actual_amount"].sum()), 2),
        round(float(variance_df["budget_amount"].sum()), 2),
        int(anomaly_summary.get("total_anomalies", 0)),
    )

    if st.session_state.get("commentary_signature") != signature:
        st.session_state["commentary_signature"] = signature
        st.session_state["commentary"] = generate_commentary(
            variance_df, anomaly_summary, dept_df
        )

if st.session_state.get("analysis_ran", False):
    variance_df = st.session_state["variance_df"]
    dept_df = st.session_state["dept_df"]
    trends_df = st.session_state["trends_df"]
    anomaly_summary = st.session_state["anomaly_summary"]
    risk_flags = st.session_state["risk_flags"]
    period_label = st.session_state["period_label"]
    commentary = st.session_state.get("commentary", "")

    for msg in st.session_state.get("dq_messages", []):
        st.warning(f"⚠️ Data quality check: {msg}")

    contamination_pct = anomaly_summary.get("contamination_used", 10.0)

    st.markdown(
        f"""
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px; align-items:center;">
        <span class="badge badge-gold">📅 {period_label}</span>
        <span class="badge">{len(variance_df):,} line items analyzed</span>
        <span class="badge">🎯 Sensitivity: {contamination_pct:.0f}%</span>
        <span class="badge">{anomaly_summary.get('total_anomalies', 0)} anomalies flagged</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Actual", f"${total_actual:,.0f}")
    k2.metric("📋 Total Budget", f"${total_budget:,.0f}")
    k3.metric("📊 Net Variance", f"${total_var:,.0f}", delta=f"{total_var_pct:+.2f}%")
    k4.metric("🔍 Anomalies Detected", anomaly_summary.get("total_anomalies", 0))

    if anomaly_summary["total_anomalies"] == 0:
        st.success("🟢 System Insight: Dataset is stable — no statistically significant anomalies detected.")
    else:
        st.error(f"🔴 System Insight: {anomaly_summary['total_anomalies']} anomalies detected — investigation required.")

    st.divider()

    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.markdown("### 🏢 Department Summary")
        dept_display = dept_df.copy()
        dept_display.columns = [
            "Department",
            "Actual ($)",
            "Budget ($)",
            "Variance ($)",
            "Variance %",
        ]
        dept_display["Actual ($)"] = dept_display["Actual ($)"].apply(lambda x: f"${x:,.0f}")
        dept_display["Budget ($)"] = dept_display["Budget ($)"].apply(lambda x: f"${x:,.0f}")
        dept_display["Variance ($)"] = dept_display["Variance ($)"].apply(lambda x: f"${x:,.0f}")
        dept_display["Variance %"] = dept_display["Variance %"].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(dept_display, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### ⚠️ Risk Flags")
        if risk_flags:
            for i, flag in enumerate(risk_flags, 1):
                st.warning(f"{i}. {flag}")
        else:
            st.success("✅ No material leadership risk flags identified.")

    st.divider()

    st.markdown("### 📉 Variance Waterfall - Top 10 Line Items")
    top10 = variance_df.head(10).copy()
    colors = ["#ef4444" if v < 0 else "#22c55e" for v in top10["variance_dollar"]]

    fig_waterfall = go.Figure(
        go.Bar(
            x=top10["line_item"] + "<br><span style='font-size:10px'>(" + top10["period"] + ")</span>",
            y=top10["variance_dollar"],
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.05)", width=1)),
            text=[f"${v:,.0f}" for v in top10["variance_dollar"]],
            textposition="outside",
            textfont=dict(color="#f1f5f9", size=11),
        )
    )

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
        bargap=0.35,
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.divider()

    st.markdown("### 📈 Rolling 3-Month Trend by Department")
    if not trends_df.empty:
        palette = [
            "#f59e0b", "#3b82f6", "#22c55e", "#a855f7", "#ec4899",
            "#14b8a6", "#f97316", "#64748b", "#06b6d4", "#84cc16",
        ]

        fig_trend = go.Figure()
        for i, dept in enumerate(trends_df["department"].unique()):
            d = trends_df[trends_df["department"] == dept]
            fig_trend.add_trace(
                go.Scatter(
                    x=d["period"],
                    y=d["rolling_3m_avg"],
                    mode="lines+markers",
                    name=dept,
                    line=dict(color=palette[i % len(palette)], width=2),
                    marker=dict(size=5),
                )
            )

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
            legend=dict(
                bgcolor="rgba(15,24,37,0.8)",
                bordercolor="#1e2d40",
                borderwidth=1,
            ),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    st.markdown("### 🔍 AI-Detected Anomalies")
    anomaly_df = variance_df[variance_df["is_anomaly"] == True].copy()

    if not anomaly_df.empty:
        st.markdown(
            f"""
        <div class="info-box">
            <strong style="color:#f59e0b;">{len(anomaly_df)}</strong> anomalies detected across
            <strong style="color:#f59e0b;">{len(anomaly_summary.get('departments_affected', []))}</strong> departments
            - sensitivity set to <strong style="color:#f59e0b;">{contamination_pct:.0f}%</strong> for this dataset size.
        </div>
        """,
            unsafe_allow_html=True,
        )

        display_cols = [
            "department",
            "line_item",
            "period",
            "actual_amount",
            "budget_amount",
            "variance_dollar",
            "variance_pct",
        ]

        st.dataframe(
            anomaly_df[display_cols].head(500),
            use_container_width=True,
            hide_index=True,
        )

        if len(anomaly_df) > 500:
            st.caption(
                f"Showing top 500 of {len(anomaly_df)} anomalies. Download the Excel report for the full list."
            )
    else:
        st.success("🟢 No anomalies detected — system confirms stable financial performance.")

        avg_var = anomaly_summary.get("mean_abs_variance_pct", variance_df["variance_pct"].abs().mean())
        max_var = anomaly_summary.get("max_abs_variance_pct", variance_df["variance_pct"].abs().max())
        std_var = anomaly_summary.get("std_variance_pct", variance_df["variance_pct"].std())
        stability_reason = anomaly_summary.get(
            "stability_reason",
            "Financial performance is within expected operating range."
        )

        st.markdown(
            f"""
        <div class="info-box">
            Stability Diagnostics:<br>
            • Avg variance: <strong style="color:#f59e0b;">{avg_var:.2f}%</strong><br>
            • Max variance: <strong style="color:#f59e0b;">{max_var:.2f}%</strong><br>
            • Std deviation: <strong style="color:#f59e0b;">{std_var:.2f}%</strong><br><br>
            Interpretation: {stability_reason}
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 🤖 AI-Generated Management Commentary")
    st.text_area(
        "Management Commentary",
        value=commentary,
        height=320,
        key=f"commentary_text_{period_label}",
        label_visibility="collapsed",
    )

    st.download_button(
        label="📋 Download Commentary as TXT",
        data=commentary,
        file_name=f"management_commentary_{period_label.replace(' ', '_')}.txt",
        mime="text/plain",
    )

    st.divider()

    st.markdown("### 🎯 Recommended Actions")
    if anomaly_summary["total_anomalies"] > 0:
        st.warning(
            "Investigate high-variance line items and validate whether deviations are structural, timing-related, or one-time in nature."
        )
    else:
        st.success(
            "Maintain current performance — no immediate corrective action is required based on the uploaded dataset."
        )

    st.divider()

    show_raw = st.checkbox("Show Raw Variance Data", key="show_raw_variance")
    if show_raw:
        st.dataframe(variance_df.head(1000), use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 📥 Export Report")
    excel_path = os.path.join(BASE_DIR, "outputs", "variance_report.xlsx")
    os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
    generate_excel_report(variance_df, dept_df, commentary, excel_path)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Excel Report",
            data=f,
            file_name=f"variance_report_{period_label.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown(
        f"""
    <div class="info-box" style="margin-top:12px;">
        Report covers <strong style="color:#f59e0b;">{period_label}</strong> ·
        {len(variance_df):,} line items · {anomaly_summary.get('total_anomalies', 0)} anomalies ·
        3 sheets: Executive Summary, Variance Detail, AI Commentary
    </div>
    """,
        unsafe_allow_html=True,
    )
