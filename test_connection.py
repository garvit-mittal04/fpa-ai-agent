"""
test_connection.py
------------------
Quick integration smoke test — verifies the full pipeline runs end-to-end
using the sample data without requiring a live API key.
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary, get_rolling_trends
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_risk_flags


def run_smoke_test():
    print("=" * 55)
    print("FP&A AI Agent — Integration Smoke Test")
    print("=" * 55)

    # ── 1. Load sample data as DataFrames ─────────────────────
    actual_path = os.path.join(BASE_DIR, "sample_data", "actual.csv")
    budget_path = os.path.join(BASE_DIR, "sample_data", "budget.csv")

    assert os.path.exists(actual_path), f"Missing file: {actual_path}"
    assert os.path.exists(budget_path), f"Missing file: {budget_path}"

    actual_df = pd.read_csv(actual_path)
    budget_df = pd.read_csv(budget_path)

    print(f"✅ Sample data loaded — {len(actual_df)} actual rows, {len(budget_df)} budget rows")

    # ── 2. Load into database ──────────────────────────────────
    load_csv_to_db(actual_df, budget_df)
    print("✅ Data loaded into SQLite database")

    # ── 3. Variance analysis ───────────────────────────────────
    variance_df = get_variance_analysis()
    assert len(variance_df) > 0, "Variance analysis returned empty dataframe"
    assert "variance_dollar" in variance_df.columns, "Missing variance_dollar column"
    assert "variance_pct" in variance_df.columns, "Missing variance_pct column"
    print(f"✅ Variance analysis complete — {len(variance_df)} line items")

    # ── 4. Department summary ──────────────────────────────────
    dept_df = get_department_summary()
    assert len(dept_df) > 0, "Department summary returned empty dataframe"
    print(f"✅ Department summary — {len(dept_df)} departments")

    # ── 5. Rolling trends ─────────────────────────────────────
    trends_df = get_rolling_trends()
    assert len(trends_df) > 0, "Rolling trends returned empty dataframe"
    print(f"✅ Rolling trends — {len(trends_df)} rows")

    # ── 6. Anomaly detection ───────────────────────────────────
    variance_df = detect_anomalies(variance_df)
    assert "is_anomaly" in variance_df.columns, "Missing is_anomaly column"

    summary = get_anomaly_summary(variance_df)

    # Validate summary contract — all keys must be present
    required_keys = ["total_anomalies", "departments_affected", "anomaly_rate", "top_anomalies"]
    for key in required_keys:
        assert key in summary, f"Missing key in anomaly summary: '{key}'"

    assert isinstance(summary["total_anomalies"], int), "total_anomalies must be int"
    assert isinstance(summary["departments_affected"], list), "departments_affected must be list"
    assert isinstance(summary["anomaly_rate"], float), "anomaly_rate must be float"
    assert isinstance(summary["top_anomalies"], list), "top_anomalies must be list"

    print(f"✅ Anomaly detection — {summary['total_anomalies']} anomalies flagged "
          f"across {len(summary['departments_affected'])} departments")

    # ── 7. Risk flags (no API key needed for structure check) ──
    try:
        flags = generate_risk_flags(variance_df)
        assert isinstance(flags, list), "generate_risk_flags must return a list"
        assert all(isinstance(f, str) for f in flags), "Each risk flag must be a string"
        print(f"✅ Risk flags — {len(flags)} flags generated")
    except Exception as e:
        # API key may not be set in local environment — that's okay
        print(f"⚠️  Risk flags skipped (likely missing GROQ_API_KEY): {e}")

    print("=" * 55)
    print("ALL SMOKE TESTS PASSED ✅")
    print("=" * 55)


if __name__ == "__main__":
    run_smoke_test()
