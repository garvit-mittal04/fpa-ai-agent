import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(df: pd.DataFrame, contamination=0.1) -> pd.DataFrame:
    """
    Takes variance analysis dataframe and flags anomalous line items
    using Isolation Forest (unsupervised ML).
    """
    df = df.copy()

    features = df[["actual_amount", "budget_amount", "variance_dollar", "variance_pct"]].fillna(0)

    model = IsolationForest(contamination=contamination, random_state=42)
    df["anomaly_score"] = model.fit_predict(features)
    df["is_anomaly"] = df["anomaly_score"] == -1

    return df

def get_anomaly_summary(df: pd.DataFrame) -> dict:
    """
    Returns a summary of anomalies for the AI commentary agent.
    """
    anomalies = df[df["is_anomaly"] == True]

    if anomalies.empty:
        return {"count": 0, "items": []}

    items = []
    for _, row in anomalies.iterrows():
        items.append({
            "period": row["period"],
            "department": row["department"],
            "line_item": row["line_item"],
            "variance_dollar": row["variance_dollar"],
            "variance_pct": row["variance_pct"]
        })

    return {
        "count": len(anomalies),
        "items": items
    }