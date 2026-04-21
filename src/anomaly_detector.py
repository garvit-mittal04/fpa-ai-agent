"""
anomaly_detector.py
-------------------
Improved anomaly detection with smart gating:
- Avoids false anomalies on clean datasets
- Uses Isolation Forest only when variance is meaningful
- Handles NaN / inf safely
- Adds stability diagnostics for downstream UI use
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = ["actual_amount", "budget_amount", "variance_dollar", "variance_pct"]


def _auto_contamination(n_rows: int) -> float:
    """
    Scale contamination by dataset size while keeping counts actionable.
    """
    if n_rows < 200:
        return 0.08
    elif n_rows < 500:
        return 0.06
    elif n_rows < 2000:
        return 0.04
    elif n_rows < 10000:
        return 0.03
    else:
        return 0.02


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean numeric feature columns for model input.
    Replaces inf/-inf with NaN, coerces to numeric, fills missing with 0.
    """
    X = df[FEATURES].copy()

    for col in FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return X


def _get_stability_diagnostics(df: pd.DataFrame) -> dict:
    """
    Compute diagnostics used to decide whether the dataset is stable.
    """
    if len(df) == 0:
        return {
            "mean_abs_variance_pct": 0.0,
            "max_abs_variance_pct": 0.0,
            "std_variance_pct": 0.0,
            "p95_abs_variance_pct": 0.0,
            "n_rows": 0,
            "reason": "empty dataset",
        }

    variance_pct = pd.to_numeric(df["variance_pct"], errors="coerce")
    variance_pct = variance_pct.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    abs_var = variance_pct.abs()

    mean_var = float(abs_var.mean())
    max_var = float(abs_var.max())
    std_var = float(variance_pct.std()) if len(variance_pct) > 1 else 0.0
    p95_var = float(abs_var.quantile(0.95)) if len(abs_var) > 1 else max_var

    return {
        "mean_abs_variance_pct": round(mean_var, 4),
        "max_abs_variance_pct": round(max_var, 4),
        "std_variance_pct": round(0.0 if pd.isna(std_var) else std_var, 4),
        "p95_abs_variance_pct": round(p95_var, 4),
        "n_rows": int(len(df)),
        "reason": "",
    }


def _is_dataset_stable(df: pd.DataFrame) -> tuple[bool, dict]:
    """
    Detect if dataset is stable enough that anomaly detection should return no anomalies.

    Heuristics:
    - Tiny datasets should not force anomalies
    - Very low average / max variance should be treated as stable
    - 95th percentile helps avoid a single noisy row dominating the decision
    """
    diagnostics = _get_stability_diagnostics(df)

    if diagnostics["n_rows"] == 0:
        diagnostics["reason"] = "empty dataset"
        return True, diagnostics

    if diagnostics["n_rows"] < 30:
        diagnostics["reason"] = "dataset too small for reliable anomaly detection"
        return True, diagnostics

    mean_var = diagnostics["mean_abs_variance_pct"]
    max_var = diagnostics["max_abs_variance_pct"]
    std_var = diagnostics["std_variance_pct"]
    p95_var = diagnostics["p95_abs_variance_pct"]

    if mean_var < 2.0 and max_var < 5.0 and std_var < 2.0:
        diagnostics["reason"] = "low mean, max, and spread of variance"
        return True, diagnostics

    if mean_var < 1.5 and p95_var < 4.0:
        diagnostics["reason"] = "very low typical variance across dataset"
        return True, diagnostics

    diagnostics["reason"] = "variance profile indicates meaningful dispersion"
    return False, diagnostics


def detect_anomalies(df: pd.DataFrame, contamination: float = None) -> pd.DataFrame:
    """
    Add anomaly outputs to variance dataframe.

    Returns columns:
    - is_anomaly
    - anomaly_score
    - contamination_used
    - stability_reason
    - mean_abs_variance_pct
    - max_abs_variance_pct
    - std_variance_pct
    - p95_abs_variance_pct
    """
    df = df.copy()

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for anomaly detection: {missing}")

    is_stable, diagnostics = _is_dataset_stable(df)

    # Add diagnostics to every row for transparency / UI use
    df["stability_reason"] = diagnostics["reason"]
    df["mean_abs_variance_pct"] = diagnostics["mean_abs_variance_pct"]
    df["max_abs_variance_pct"] = diagnostics["max_abs_variance_pct"]
    df["std_variance_pct"] = diagnostics["std_variance_pct"]
    df["p95_abs_variance_pct"] = diagnostics["p95_abs_variance_pct"]

    if is_stable:
        df["is_anomaly"] = False
        df["anomaly_score"] = 0.0
        df["contamination_used"] = 0.0
        return df

    if contamination is None:
        contamination = _auto_contamination(len(df))

    X = _prepare_features(df)

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )

    preds = model.fit_predict(X.values)

    df["is_anomaly"] = preds == -1
    df["anomaly_score"] = model.decision_function(X.values)
    df["contamination_used"] = round(contamination * 100, 1)

    return df


def get_anomaly_summary(df: pd.DataFrame) -> dict:
    """
    Return a stable summary contract used by app.py and commentary_agent.py.
    """
    if "is_anomaly" not in df.columns:
        return {
            "total_anomalies": 0,
            "departments_affected": [],
            "anomaly_rate": 0.0,
            "top_anomalies": [],
            "contamination_used": 0.0,
            "stability_reason": "",
            "mean_abs_variance_pct": 0.0,
            "max_abs_variance_pct": 0.0,
            "std_variance_pct": 0.0,
            "p95_abs_variance_pct": 0.0,
        }

    anomalies = df[df["is_anomaly"] == True]
    total = int(len(anomalies))
    departments = sorted(anomalies["department"].unique().tolist()) if total > 0 else []
    rate = round(total / len(df) * 100, 1) if len(df) > 0 else 0.0

    contamination_used = float(df["contamination_used"].iloc[0]) if "contamination_used" in df.columns else 0.0
    stability_reason = str(df["stability_reason"].iloc[0]) if "stability_reason" in df.columns else ""
    mean_abs_variance_pct = float(df["mean_abs_variance_pct"].iloc[0]) if "mean_abs_variance_pct" in df.columns else 0.0
    max_abs_variance_pct = float(df["max_abs_variance_pct"].iloc[0]) if "max_abs_variance_pct" in df.columns else 0.0
    std_variance_pct = float(df["std_variance_pct"].iloc[0]) if "std_variance_pct" in df.columns else 0.0
    p95_abs_variance_pct = float(df["p95_abs_variance_pct"].iloc[0]) if "p95_abs_variance_pct" in df.columns else 0.0

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
        "stability_reason": stability_reason,
        "mean_abs_variance_pct": round(mean_abs_variance_pct, 2),
        "max_abs_variance_pct": round(max_abs_variance_pct, 2),
        "std_variance_pct": round(std_variance_pct, 2),
        "p95_abs_variance_pct": round(p95_abs_variance_pct, 2),
    }
