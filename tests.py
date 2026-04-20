import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary, get_rolling_trends
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_risk_flags

ACTUALS = os.path.join(BASE_DIR, "sample_data/actual.csv")
BUDGET = os.path.join(BASE_DIR, "sample_data/budget.csv")

def test_data_loading():
    print("TEST 1: Data Loading...")
    load_csv_to_db(ACTUALS, BUDGET)
    print("  ✅ Data loaded successfully\n")

def test_variance_analysis():
    print("TEST 2: Variance Analysis...")
    df = get_variance_analysis()
    assert len(df) > 0, "Variance dataframe is empty"
    assert "variance_dollar" in df.columns, "Missing variance_dollar column"
    assert "variance_pct" in df.columns, "Missing variance_pct column"
    assert df["actual_amount"].notnull().all(), "Null values in actual_amount"
    assert df["budget_amount"].notnull().all(), "Null values in budget_amount"
    print(f"  ✅ {len(df)} variance records returned")
    print(f"  ✅ Largest unfavorable: ${df[df['variance_dollar']<0]['variance_dollar'].min():,.0f}")
    print(f"  ✅ Largest favorable: ${df[df['variance_dollar']>0]['variance_dollar'].max():,.0f}\n")

def test_department_summary():
    print("TEST 3: Department Summary...")
    df = get_department_summary()
    assert len(df) == 6, f"Expected 6 departments, got {len(df)}"
    assert "total_actual" in df.columns, "Missing total_actual"
    assert "variance_pct" in df.columns, "Missing variance_pct"
    print(f"  ✅ {len(df)} departments summarized")
    for _, row in df.iterrows():
        print(f"  📊 {row['department']}: ${row['total_actual']:,.0f} actual | {row['variance_pct']}% variance")
    print()

def test_rolling_trends():
    print("TEST 4: Rolling Trend Analysis...")
    df = get_rolling_trends()
    assert len(df) > 0, "Trends dataframe is empty"
    assert "rolling_3m_avg" in df.columns, "Missing rolling_3m_avg"
    assert "actual_amount" in df.columns, "Missing actual_amount"
    print(f"  ✅ {len(df)} trend records returned")
    print(f"  ✅ Periods covered: {sorted(df['period'].unique())}\n")

def test_anomaly_detection():
    print("TEST 5: Anomaly Detection...")
    df = get_variance_analysis()
    df = detect_anomalies(df)
    summary = get_anomaly_summary(df)
    assert "is_anomaly" in df.columns, "Missing is_anomaly column"
    assert summary["count"] >= 0, "Invalid anomaly count"
    print(f"  ✅ {summary['count']} anomalies detected out of {len(df)} records")
    if summary["count"] > 0:
        for item in summary["items"][:3]:
            print(f"  ⚠️  {item['period']} | {item['department']} | {item['line_item']} | ${item['variance_dollar']:,.0f}")
    print()

def test_risk_flags():
    print("TEST 6: Risk Flag Detection...")
    df = get_variance_analysis()
    flags = generate_risk_flags(df)
    assert isinstance(flags, list), "Risk flags should be a list"
    print(f"  ✅ {len(flags)} risk flags identified (>10% variance threshold)")
    for f in flags[:5]:
        print(f"  🚩 {f['period']} | {f['item']} | {f['message']}")
    print()

def test_data_integrity():
    print("TEST 7: Data Integrity Checks...")
    df = get_variance_analysis()
    df["calculated_var"] = df["actual_amount"] - df["budget_amount"]
    diff = abs(df["variance_dollar"] - df["calculated_var"]).max()
    assert diff < 0.01, f"Variance calculation error: max diff = {diff}"
    assert (df["actual_amount"] >= 0).all(), "Negative actual amounts found"
    assert df["period"].nunique() == 12, f"Expected 12 periods, got {df['period'].nunique()}"
    assert df["department"].nunique() == 6, f"Expected 6 departments, got {df['department'].nunique()}"
    print(f"  ✅ Variance math verified — max error: {diff:.6f}")
    print(f"  ✅ No negative amounts found")
    print(f"  ✅ All 12 periods present")
    print(f"  ✅ All 6 departments present\n")

if __name__ == "__main__":
    print("=" * 55)
    print("   FP&A AI AGENT — TEST SUITE")
    print("=" * 55 + "\n")

    load_csv_to_db(ACTUALS, BUDGET)

    test_data_loading()
    test_variance_analysis()
    test_department_summary()
    test_rolling_trends()
    test_anomaly_detection()
    test_risk_flags()
    test_data_integrity()

    print("=" * 55)
    print("   ALL TESTS PASSED ✅")
    print("=" * 55)