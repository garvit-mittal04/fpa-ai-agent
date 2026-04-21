"""
anomaly_detector.py
-------------------
Uses Isolation Forest (unsupervised ML) to flag statistically unusual
line items in the variance dataset.

Why Isolation Forest?
- No labeled training data required — ideal for financial data where
  "normal" varies by department and period.
- Handles multivariate outliers across amount, budget, and variance features.

Contamination scaling:
- For small datasets (<500 rows)  : 10% — aggressive flagging, manageable count
- For medium datasets (500–2000)  :  5% — balanced
- For large datasets (2000–10000) :  3% — keeps flagged items actionable
- For very large (>10000 rows)    :  2% — prevents overwhelming anomaly lists

What counts as a good anomaly?
- A line item where the combination of actual_amount, budget_amount,
  variance_dollar, and variance_pct is statistically unusual relative
  to the rest of the dataset.
- Not just large variance — a $500K overspend in a $10M budget line
  may be normal; the same in a $50K line is anomalous.
"""

import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = ["actual_amount", "budget_amount", "variance_dollar", "variance_pct"]


def _auto_contamination(n_rows: int) -> float:
    """
    Return a contamination rate scaled to dataset size so the number of
    flagged anomalies stays actionable regardless of how many rows are uploaded.

    Size thresholds:
        < 500 rows   → 10%  (small monthly dataset, flag broadly)
        500–2000     →  5%  (standard monthly close)
        2000–10000   →  3%  (multi-period or multi-department dataset)
        > 10000      →  2%  (large historical dataset)
    """
    if n_rows < 500:
        return 0.10
    elif n_rows < 2000:
        return 0.05
    elif n_rows < 10000:
        return 0.03
    else:
        return 0.02


def detect_anomalies(df: pd.DataFrame, contamination: float = None) -> pd.DataFrame:
    """
    Add is_anomaly (bool) and anomaly_score (float) columns to variance dataframe.

    Parameters
    ----------
    df            : DataFrame with actual_amount, budget_amount, variance_dollar, variance_pct
    contamination : expected proportion of anomalies.
                    If None (default), rate is chosen automatically based on dataset size.

    Returns
    -------
    DataFrame with two new columns: is_anomaly, anomaly_score
    """
    df = df.copy()

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for anomaly detection: {missing}")

    # Auto-scale contamination if not explicitly provided
    if contamination is None:
        contamination = _auto_contamination(len(df))

    X = df[FEATURES].fillna(0).values
    model = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    preds = model.fit_predict(X)

    df["is_anomaly"] = preds == -1                         # -1 = anomaly, 1 = normal
    df["anomaly_score"] = model.decision_function(X)       # lower = more anomalous
    df["contamination_used"] = round(contamination * 100, 1)   # surfaced for UI transparency

    return df


def get_anomaly_summary(df: pd.DataFrame) -> dict:
    """
    Return a summary dict with a stable contract used by app.py and commentary_agent.py.

    Keys
    ----
    total_anomalies      : int   — count of flagged rows
    departments_affected : list  — departments with at least one anomaly
    anomaly_rate         : float — anomalies / total rows * 100
    top_anomalies        : list  — top 3 anomalies [{department, line_item,
                                    variance_dollar, variance_pct}]
    contamination_used   : float — contamination % actually applied (for display)
    """
    if "is_anomaly" not in df.columns:
        return {
            "total_anomalies": 0,
            "departments_affected": [],
            "anomaly_rate": 0.0,
            "top_anomalies": [],
            "contamination_used": 0.0,
        }

    anomalies = df[df["is_anomaly"] == True]
    total = int(len(anomalies))
    departments = sorted(anomalies["department"].unique().tolist()) if total > 0 else []
    rate = round(total / len(df) * 100, 1) if len(df) > 0 else 0.0

    # Pull contamination_used from the df if available
    contamination_used = float(df["contamination_used"].iloc[0]) if "contamination_used" in df.columns else 0.0

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
        "contamination_used": contamination_used,
    }
