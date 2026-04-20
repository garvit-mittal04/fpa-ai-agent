"""
anomaly_detector.py
-------------------
Uses Isolation Forest (unsupervised ML) to flag statistically unusual
line items in the variance dataset.

Why Isolation Forest?
- No labeled training data required — ideal for financial data where
  "normal" varies by department and period.
- Handles multivariate outliers across amount, budget, and variance features.
- contamination=0.1 means ~10% of records are expected to be anomalous,
  which is a reasonable prior for a monthly close dataset.

What counts as a good anomaly?
- A line item where the combination of actual_amount, budget_amount,
  variance_dollar, and variance_pct is statistically unusual relative
  to the rest of the dataset.
- Not just large variance — a $500K overspend in a $10M budget line
  may be normal; the same in a $50K line is anomalous.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


FEATURES = ["actual_amount", "budget_amount", "variance_dollar", "variance_pct"]


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.1) -> pd.DataFrame:
    """
    Add an `is_anomaly` boolean column to the variance dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Variance dataframe with columns: actual_amount, budget_amount,
        variance_dollar, variance_pct.
    contamination : float
        Expected proportion of anomalies in the dataset (default 0.1 = 10%).

    Returns
    -------
    pd.DataFrame
        Original dataframe with `is_anomaly` column added.
    """
    df = df.copy()

    # Validate required columns exist
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for anomaly detection: {missing}")

    X = df[FEATURES].fillna(0).values

    model = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    preds = model.fit_predict(X)

    # IsolationForest returns -1 for anomalies, 1 for normal
    df["is_anomaly"] = preds == -1
    df["anomaly_score"] = model.decision_function(X)  # lower = more anomalous

    return df


def get_anomaly_summary(df: pd.DataFrame) -> dict:
    """
    Build a summary dict with keys used by both app.py and commentary_agent.py.

    Keys returned
    -------------
    total_anomalies      : int   — count of flagged rows
    departments_affected : list  — unique departments with at least one anomaly
    anomaly_rate         : float — anomalies / total rows * 100
    top_anomalies        : list  — top 3 anomalies as dicts with dept/item/variance
    """
    if "is_anomaly" not in df.columns:
        return {
            "total_anomalies": 0,
            "departments_affected": [],
            "anomaly_rate": 0.0,
            "top_anomalies": [],
        }

    anomalies = df[df["is_anomaly"] == True]

    total = int(len(anomalies))
    departments = sorted(anomalies["department"].unique().tolist()) if total > 0 else []
    rate = round(total / len(df) * 100, 1) if len(df) > 0 else 0.0

    # Top 3 by absolute variance dollar
    top = []
    if total > 0:
        top_rows = anomalies.reindex(
            anomalies["variance_dollar"].abs().sort_values(ascending=False).index
        ).head(3)
        for _, row in top_rows.iterrows():
            top.append({
                "department": row.get("department", ""),
                "line_item": row.get("line_item", ""),
                "variance_dollar": round(float(row.get("variance_dollar", 0)), 2),
                "variance_pct": round(float(row.get("variance_pct", 0)), 2),
            })

    return {
        "total_anomalies": total,
        "departments_affected": departments,
        "anomaly_rate": rate,
        "top_anomalies": top,
    }
