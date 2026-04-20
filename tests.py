"""
tests.py
--------
Unit and integration tests for the FP&A AI Agent.
Run with: python tests.py

Tests cover:
  - Data loading and schema validation
  - Variance calculations (math correctness)
  - Anomaly summary contract (keys and types)
  - Department summary structure
  - Rolling trends structure
  - Report generation (without API calls)
  - Data integrity checks
  - Error handling (malformed inputs)
"""

import os
import sys
import pandas as pd
import numpy as np
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary, get_rolling_trends
from anomaly_detector import detect_anomalies, get_anomaly_summary
from report_generator import generate_excel_report

PASS = "✅"
FAIL = "❌"
results = []


def run_test(name, fn):
    try:
        fn()
        print(f"{PASS} {name}")
        results.append((name, True, None))
    except Exception as e:
        print(f"{FAIL} {name} — {e}")
        results.append((name, False, str(e)))


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_sample_data(n_periods=3, n_depts=2, n_items=4):
    """Generate minimal synthetic actuals and budget dataframes for testing."""
    periods = [f"2023-{str(i+1).zfill(2)}" for i in range(n_periods)]
    depts = [f"Dept_{i}" for i in range(n_depts)]
    items = [f"Item_{i}" for i in range(n_items)]

    rows = []
    for period in periods:
        for dept in depts:
            for item in items:
                rows.append({
                    "department": dept,
                    "line_item": item,
                    "period": period,
                    "amount": np.random.uniform(10000, 100000),
                    "data_type": "actual"
                })

    actual_df = pd.DataFrame(rows).drop(columns=["data_type"])
    budget_df = actual_df.copy()
    budget_df["amount"] = budget_df["amount"] * np.random.uniform(0.85, 1.15, len(budget_df))
    return actual_df, budget_df


def load_sample_to_db():
    actual_path = os.path.join(BASE_DIR, "sample_data", "actual.csv")
    budget_path = os.path.join(BASE_DIR, "sample_data", "budget.csv")
    actual_df = pd.read_csv(actual_path)
    budget_df = pd.read_csv(budget_path)
    load_csv_to_db(actual_df, budget_df)
    return actual_df, budget_df


# ─── TEST 1: Data Loading ──────────────────────────────────────────────────────

def test_data_loading():
    actual_df, budget_df = load_sample_to_db()
    assert len(actual_df) > 0, "Actuals dataframe is empty"
    assert len(budget_df) > 0, "Budget dataframe is empty"
    required_cols = {"department", "line_item", "period", "amount"}
    assert required_cols.issubset(set(actual_df.columns)), \
        f"Missing columns in actuals: {required_cols - set(actual_df.columns)}"
    assert required_cols.issubset(set(budget_df.columns)), \
        f"Missing columns in budget: {required_cols - set(budget_df.columns)}"


# ─── TEST 2: Variance Analysis Structure ──────────────────────────────────────

def test_variance_analysis_structure():
    load_sample_to_db()
    df = get_variance_analysis()
    assert len(df) > 0, "Variance analysis returned empty result"
    required = {"department", "line_item", "period", "actual_amount", "budget_amount",
                "variance_dollar", "variance_pct"}
    missing = required - set(df.columns)
    assert not missing, f"Variance analysis missing columns: {missing}"


# ─── TEST 3: Variance Math Correctness ────────────────────────────────────────

def test_variance_math():
    load_sample_to_db()
    df = get_variance_analysis()

    # variance_dollar = actual - budget
    computed = (df["actual_amount"] - df["budget_amount"]).round(2)
    actual_var = df["variance_dollar"].round(2)
    max_error = (computed - actual_var).abs().max()
    assert max_error < 0.01, f"Variance dollar math error: max error = {max_error}"

    # variance_pct = variance_dollar / budget * 100
    non_zero = df[df["budget_amount"] != 0].copy()
    computed_pct = (non_zero["variance_dollar"] / non_zero["budget_amount"] * 100).round(2)
    actual_pct = non_zero["variance_pct"].round(2)
    max_pct_error = (computed_pct - actual_pct).abs().max()
    assert max_pct_error < 0.1, f"Variance pct math error: max error = {max_pct_error}"


# ─── TEST 4: Department Summary Structure ─────────────────────────────────────

def test_department_summary():
    load_sample_to_db()
    df = get_department_summary()
    assert len(df) > 0, "Department summary is empty"
    assert len(df) == 6, f"Expected 6 departments, got {len(df)}"
    assert df.shape[1] >= 4, "Department summary should have at least 4 columns"


# ─── TEST 5: Rolling Trends Structure ─────────────────────────────────────────

def test_rolling_trends():
    load_sample_to_db()
    df = get_rolling_trends()
    assert len(df) > 0, "Rolling trends returned empty result"
    assert "rolling_3m_avg" in df.columns, "Missing rolling_3m_avg column"
    assert "period" in df.columns, "Missing period column"
    assert "department" in df.columns, "Missing department column"


# ─── TEST 6: Anomaly Detection Output ─────────────────────────────────────────

def test_anomaly_detection():
    load_sample_to_db()
    variance_df = get_variance_analysis()
    result = detect_anomalies(variance_df)
    assert "is_anomaly" in result.columns, "Missing is_anomaly column"
    assert "anomaly_score" in result.columns, "Missing anomaly_score column"
    assert result["is_anomaly"].dtype == bool, "is_anomaly should be boolean"
    anomaly_count = result["is_anomaly"].sum()
    assert anomaly_count > 0, "Expected at least 1 anomaly in sample data"
    assert anomaly_count < len(result), "All rows flagged as anomalies — check contamination setting"


# ─── TEST 7: Anomaly Summary Contract ─────────────────────────────────────────

def test_anomaly_summary_contract():
    """
    Critical: verifies the exact keys returned by get_anomaly_summary()
    match what app.py and commentary_agent.py expect.
    """
    load_sample_to_db()
    variance_df = get_variance_analysis()
    variance_df = detect_anomalies(variance_df)
    summary = get_anomaly_summary(variance_df)

    # Keys used by app.py
    assert "total_anomalies" in summary, "app.py needs 'total_anomalies'"

    # Keys used by commentary_agent.py
    assert "departments_affected" in summary, "commentary_agent.py needs 'departments_affected'"

    # Type checks
    assert isinstance(summary["total_anomalies"], int), \
        f"total_anomalies must be int, got {type(summary['total_anomalies'])}"
    assert isinstance(summary["departments_affected"], list), \
        f"departments_affected must be list, got {type(summary['departments_affected'])}"
    assert isinstance(summary["anomaly_rate"], float), \
        f"anomaly_rate must be float, got {type(summary['anomaly_rate'])}"
    assert isinstance(summary["top_anomalies"], list), \
        f"top_anomalies must be list, got {type(summary['top_anomalies'])}"

    # top_anomalies structure
    for item in summary["top_anomalies"]:
        assert "department" in item, "top_anomaly item missing 'department'"
        assert "line_item" in item, "top_anomaly item missing 'line_item'"
        assert "variance_dollar" in item, "top_anomaly item missing 'variance_dollar'"


# ─── TEST 8: Report Generation (no API calls) ─────────────────────────────────

def test_report_generation():
    load_sample_to_db()
    variance_df = get_variance_analysis()
    dept_df = get_department_summary()
    variance_df = detect_anomalies(variance_df)
    commentary = "Test commentary — no API call required."

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_report.xlsx")
        generate_excel_report(variance_df, dept_df, commentary, output_path)
        assert os.path.exists(output_path), "Excel report file was not created"
        assert os.path.getsize(output_path) > 1000, "Excel report file is suspiciously small"


# ─── TEST 9: Malformed Input Handling ─────────────────────────────────────────

def test_malformed_csv_handling():
    """Verify detect_anomalies raises a clear error on missing columns."""
    bad_df = pd.DataFrame({"col_a": [1, 2], "col_b": [3, 4]})
    try:
        detect_anomalies(bad_df)
        raise AssertionError("Should have raised ValueError on missing columns")
    except ValueError as e:
        assert "Missing required columns" in str(e), \
            f"Expected clear error message, got: {e}"


# ─── TEST 10: Empty Data Handling ─────────────────────────────────────────────

def test_empty_anomaly_summary():
    """get_anomaly_summary on a dataframe with no is_anomaly column returns safe defaults."""
    df = pd.DataFrame({"department": ["Sales"], "variance_dollar": [1000]})
    summary = get_anomaly_summary(df)
    assert summary["total_anomalies"] == 0
    assert summary["departments_affected"] == []
    assert summary["top_anomalies"] == []


# ─── TEST 11: Data Integrity ──────────────────────────────────────────────────

def test_data_integrity():
    load_sample_to_db()
    variance_df = get_variance_analysis()

    # No negative actual amounts
    neg = (variance_df["actual_amount"] < 0).sum()
    assert neg == 0, f"Found {neg} negative actual amounts"

    # All 12 periods present
    periods = variance_df["period"].nunique()
    assert periods == 12, f"Expected 12 periods, found {periods}"

    # All 6 departments present
    depts = variance_df["department"].nunique()
    assert depts == 6, f"Expected 6 departments, found {depts}"


# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("FP&A AI Agent — Test Suite")
    print("=" * 55)

    run_test("1.  Data loading", test_data_loading)
    run_test("2.  Variance analysis structure", test_variance_analysis_structure)
    run_test("3.  Variance math correctness", test_variance_math)
    run_test("4.  Department summary structure", test_department_summary)
    run_test("5.  Rolling trends structure", test_rolling_trends)
    run_test("6.  Anomaly detection output", test_anomaly_detection)
    run_test("7.  Anomaly summary contract", test_anomaly_summary_contract)
    run_test("8.  Report generation (no API)", test_report_generation)
    run_test("9.  Malformed input handling", test_malformed_csv_handling)
    run_test("10. Empty data handling", test_empty_anomaly_summary)
    run_test("11. Data integrity", test_data_integrity)

    print("=" * 55)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")
    if failed == 0:
        print("ALL TESTS PASSED ✅")
    else:
        print("SOME TESTS FAILED ❌")
        for name, ok, err in results:
            if not ok:
                print(f"  — {name}: {err}")
    print("=" * 55)
