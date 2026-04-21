"""
anomaly_detector.py
-------------------
Improved anomaly detection with "smart gating":
- Avoids false anomalies on clean datasets
- Uses Isolation Forest only when variance is meaningful
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = ["actual_amount", "budget_amount", "variance_dollar", "variance_pct"]


def _auto_contamination(n_rows: int) -> float:
    if n_rows < 500:
        return 0.10
    elif n_rows < 2000:
        return 0.05
    elif n_rows < 10000:
        return 0.03
    else:
        return 0.02


def _is_dataset_stable(df: pd.DataFrame) -> bool:
    """
    Detect if dataset is too stable (no real anomalies).

    Criteria:
    - Very low variance %
    - No extreme outliers
    """
    if len(df) == 0:
        return True

    # Mean absolute variance %
    mean_var = df["variance_pct"].abs().mean()

    # Max variance %
    max_var = df["variance_pct"].abs().max()

    # Std deviation of variance
    std_var = df["variance_pct"].std()

    # Heuristics tuned for finance datasets
    if mean_var < 2 and max_var < 5 and std_var < 2:
        return True

    return False


def detect_anomalies(df: pd.DataFrame, contamination: float = None) -> pd.DataFrame:
    df = df.copy()

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for anomaly detection: {missing}")

    # 🔥 STEP 1: Check if dataset is stable
    if _is_dataset_stable(df):
        df["is_anomaly"] = False
        df["anomaly_score"] = 0.0
        df["contamination_used"] = 0.0
        return df

    # STEP 2: Normal anomaly detection
    if contamination is None:
        contamination = _auto_contamination(len(df))

    X = df[FEATURES].fillna(0).values

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )

    preds = model.fit_predict(X)

    df["is_anomaly"] = preds == -1
    df["anomaly_score"] = model.decision_function(X)
    df["contamination_used"] = round(contamination * 100, 1)

    return df


def get_anomaly_summary(df: pd.DataFrame) -> dict:
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
