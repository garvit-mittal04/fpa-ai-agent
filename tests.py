"""
tests.py
--------
Unit and integration tests for the FP&A AI Agent.
Run with: python3 tests.py

Tests cover:
  - Data loading and schema validation
  - Variance calculations (math correctness)
  - Budget-only row coverage (no silent data loss)
  - Anomaly summary contract (keys and types)
  - Department summary structure
  - Rolling trends structure
  - Report generation (no API calls required)
  - Data integrity checks
  - Input validation (malformed CSV)
  - Empty data handling
  - Risk flags return list of strings
"""

import os
import sys
import pandas as pd
import numpy as np
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from sql_engine import (
    load_csv_to_db, get_variance_analysis, get_department_summary,
    get_rolling_trends, validate_schema,
)
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_risk_flags
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


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_sample():
    actual_df = pd.read_csv(os.path.join(BASE_DIR, "sample_data", "actual.csv"))
    budget_df = pd.read_csv(os.path.join(BASE_DIR, "sample_data", "budget.csv"))
    load_csv_to_db(actual_df, budget_df)
    return actual_df, budget_df


# ─── TEST 1: Schema validation — good data ────────────────────────────────────

def test_schema_validation_pass():
    df = pd.DataFrame({
        "department": ["Sales"], "line_item": ["Revenue"],
        "period": ["2023-01"], "amount": [100000],
    })
    validate_schema(df, "Test")   # should not raise


# ─── TEST 2: Schema validation — bad data ─────────────────────────────────────

def test_schema_validation_fail():
    bad = pd.DataFrame({"col_a": [1], "col_b": [2]})
    try:
        validate_schema(bad, "Test")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "missing required columns" in str(e).lower()


# ─── TEST 3: Data loading ─────────────────────────────────────────────────────

def test_data_loading():
    actual_df, budget_df = load_sample()
    assert len(actual_df) > 0
    assert len(budget_df) > 0


# ─── TEST 4: Variance analysis structure ──────────────────────────────────────

def test_variance_analysis_structure():
    load_sample()
    df = get_variance_analysis()
    assert len(df) > 0
    required = {"department", "line_item", "period",
                "actual_amount", "budget_amount", "variance_dollar", "variance_pct"}
    assert not required - set(df.columns), f"Missing: {required - set(df.columns)}"


# ─── TEST 5: Variance math correctness ────────────────────────────────────────

def test_variance_math():
    load_sample()
    df = get_variance_analysis()
    computed = (df["actual_amount"] - df["budget_amount"]).round(2)
    max_error = (computed - df["variance_dollar"].round(2)).abs().max()
    assert max_error < 0.01, f"Variance dollar error: {max_error}"


# ─── TEST 6: Budget-only rows are not lost ────────────────────────────────────

def test_budget_only_rows_preserved():
    """
    Inject a budget row with no matching actual.
    The variance query must return it with actual_amount = 0.
    """
    actual_df = pd.read_csv(os.path.join(BASE_DIR, "sample_data", "actual.csv"))
    budget_df = pd.read_csv(os.path.join(BASE_DIR, "sample_data", "budget.csv"))

    extra_budget = pd.DataFrame([{
        "department": "TestDept",
        "line_item":  "BudgetOnlyLine",
        "period":     "2099-01",
        "amount":     99999,
    }])
    budget_df = pd.concat([budget_df, extra_budget], ignore_index=True)
    load_csv_to_db(actual_df, budget_df)

    df = get_variance_analysis()
    row = df[(df["department"] == "TestDept") & (df["line_item"] == "BudgetOnlyLine")]
    assert len(row) == 1, "Budget-only row was lost in variance analysis"
    assert float(row.iloc[0]["actual_amount"]) == 0.0, "actual_amount should be 0 for budget-only row"
    assert float(row.iloc[0]["budget_amount"]) == 99999.0


# ─── TEST 7: Department summary ───────────────────────────────────────────────

def test_department_summary():
    load_sample()
    df = get_department_summary()
    assert len(df) > 0
    assert len(df) == 6, f"Expected 6 departments, got {len(df)}"


# ─── TEST 8: Rolling trends ───────────────────────────────────────────────────

def test_rolling_trends():
    load_sample()
    df = get_rolling_trends()
    assert len(df) > 0
    assert "rolling_3m_avg" in df.columns
    assert "period" in df.columns


# ─── TEST 9: Anomaly detection ────────────────────────────────────────────────

def test_anomaly_detection():
    load_sample()
    df = detect_anomalies(get_variance_analysis())
    assert "is_anomaly" in df.columns
    assert df["is_anomaly"].dtype == bool
    assert df["is_anomaly"].sum() > 0, "Expected at least 1 anomaly"


# ─── TEST 10: Anomaly summary contract ────────────────────────────────────────

def test_anomaly_summary_contract():
    """Verify exact keys and types used by app.py and commentary_agent.py."""
    load_sample()
    df = detect_anomalies(get_variance_analysis())
    s  = get_anomaly_summary(df)

    # Keys used by app.py
    assert "total_anomalies" in s,      "app.py needs 'total_anomalies'"
    # Keys used by commentary_agent.py
    assert "departments_affected" in s, "commentary_agent.py needs 'departments_affected'"

    assert isinstance(s["total_anomalies"],      int),   "total_anomalies must be int"
    assert isinstance(s["departments_affected"], list),  "departments_affected must be list"
    assert isinstance(s["anomaly_rate"],         float), "anomaly_rate must be float"
    assert isinstance(s["top_anomalies"],        list),  "top_anomalies must be list"

    for item in s["top_anomalies"]:
        assert "department"      in item
        assert "line_item"       in item
        assert "variance_dollar" in item


# ─── TEST 11: Risk flags return list of strings ───────────────────────────────

def test_risk_flags_are_strings():
    """generate_risk_flags must return a list of strings, never dicts."""
    load_sample()
    df    = get_variance_analysis()
    flags = generate_risk_flags(df)
    assert isinstance(flags, list), "generate_risk_flags must return list"
    assert len(flags) > 0,          "Expected at least one risk flag"
    for flag in flags:
        assert isinstance(flag, str), \
            f"Each risk flag must be a string, got {type(flag)}: {flag}"


# ─── TEST 12: Report generation (no API) ─────────────────────────────────────

def test_report_generation():
    load_sample()
    variance_df = detect_anomalies(get_variance_analysis())
    dept_df     = get_department_summary()
    commentary  = "Test commentary — no API call required."

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_report.xlsx")
        generate_excel_report(variance_df, dept_df, commentary, path)
        assert os.path.exists(path),         "Excel file not created"
        assert os.path.getsize(path) > 1000, "Excel file suspiciously small"


# ─── TEST 13: Empty anomaly summary safe defaults ────────────────────────────

def test_empty_anomaly_summary():
    df = pd.DataFrame({"department": ["Sales"], "variance_dollar": [1000]})
    s  = get_anomaly_summary(df)
    assert s["total_anomalies"]      == 0
    assert s["departments_affected"] == []
    assert s["top_anomalies"]        == []


# ─── TEST 14: Data integrity ─────────────────────────────────────────────────

def test_data_integrity():
    load_sample()
    df = get_variance_analysis()
    assert (df["actual_amount"] < 0).sum() == 0, "Negative actual amounts found"
    assert df["period"].nunique()     == 12, f"Expected 12 periods"
    assert df["department"].nunique() == 6,  f"Expected 6 departments"

# ─── TEST 15: Budget-only department preserved in department summary ──────────

def test_budget_only_dept_in_summary():
    actual_df = pd.read_csv(os.path.join(BASE_DIR, "sample_data", "actual.csv"))
    budget_df = pd.read_csv(os.path.join(BASE_DIR, "sample_data", "budget.csv"))

    extra_budget = pd.DataFrame([{
        "department": "GhostDept",
        "line_item":  "PlannedExpense",
        "period":     "2099-01",
        "amount":     50000,
    }])
    budget_df = pd.concat([budget_df, extra_budget], ignore_index=True)
    load_csv_to_db(actual_df, budget_df)

    df = get_department_summary()
    row = df[df["department"] == "GhostDept"]
    assert len(row) == 1, "Budget-only department was lost in department summary"
    assert float(row.iloc[0]["total_actual"]) == 0.0, "total_actual should be 0 for budget-only department"
    assert float(row.iloc[0]["total_budget"]) == 50000.0
# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("FP&A AI Agent — Test Suite")
    print("=" * 55)

    run_test("1.  Schema validation — good data",        test_schema_validation_pass)
    run_test("2.  Schema validation — bad data",         test_schema_validation_fail)
    run_test("3.  Data loading",                         test_data_loading)
    run_test("4.  Variance analysis structure",          test_variance_analysis_structure)
    run_test("5.  Variance math correctness",            test_variance_math)
    run_test("6.  Budget-only rows preserved",           test_budget_only_rows_preserved)
    run_test("7.  Department summary structure",         test_department_summary)
    run_test("8.  Rolling trends structure",             test_rolling_trends)
    run_test("9.  Anomaly detection output",             test_anomaly_detection)
    run_test("10. Anomaly summary contract",             test_anomaly_summary_contract)
    run_test("11. Risk flags are strings",               test_risk_flags_are_strings)
    run_test("12. Report generation (no API)",           test_report_generation)
    run_test("13. Empty anomaly summary safe defaults",  test_empty_anomaly_summary)
    run_test("14. Data integrity",                       test_data_integrity)
    run_test("15. Budget-only dept preserved in summary", test_budget_only_dept_in_summary)
    
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