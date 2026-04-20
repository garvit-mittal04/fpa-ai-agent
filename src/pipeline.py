"""
pipeline.py
-----------
Orchestrates the full FP&A analysis pipeline.
Keeps app.py free of business logic — all data
processing flows through run_pipeline().
"""

import os
import pandas as pd

from sql_engine import (
    load_csv_to_db,
    get_variance_analysis,
    get_department_summary,
    get_rolling_trends,
)
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_commentary, generate_risk_flags


def run_pipeline(actual_df: pd.DataFrame, budget_df: pd.DataFrame) -> dict:
    """
    Execute the full analysis pipeline.

    Parameters
    ----------
    actual_df : pd.DataFrame  — validated actuals data
    budget_df : pd.DataFrame  — validated budget data

    Returns
    -------
    dict with keys:
        variance_df      : pd.DataFrame  — variance analysis with anomaly flags
        dept_df          : pd.DataFrame  — department-level summary
        trends_df        : pd.DataFrame  — rolling 3-month trends
        anomaly_summary  : dict          — anomaly stats contract
        risk_flags       : list[str]     — LLM or rule-based risk flags
    """
    load_csv_to_db(actual_df, budget_df)

    variance_df     = get_variance_analysis()
    dept_df         = get_department_summary()
    trends_df       = get_rolling_trends()
    variance_df     = detect_anomalies(variance_df)
    anomaly_summary = get_anomaly_summary(variance_df)
    risk_flags      = generate_risk_flags(variance_df)

    return {
        "variance_df":     variance_df,
        "dept_df":         dept_df,
        "trends_df":       trends_df,
        "anomaly_summary": anomaly_summary,
        "risk_flags":      risk_flags,
    }


def run_commentary(results: dict) -> str:
    """
    Generate AI management commentary from pipeline results.

    Separated from run_pipeline() so the UI can show the dashboard
    immediately and stream the commentary independently.
    """
    return generate_commentary(
        results["variance_df"],
        results["anomaly_summary"],
        results["dept_df"],
    )
