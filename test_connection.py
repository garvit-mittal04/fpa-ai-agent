import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from sql_engine import load_csv_to_db, get_variance_analysis, get_department_summary
from anomaly_detector import detect_anomalies, get_anomaly_summary
from commentary_agent import generate_commentary, generate_risk_flags

# Load data
load_csv_to_db(
    os.path.join(BASE_DIR, "sample_data/actual.csv"),
    os.path.join(BASE_DIR, "sample_data/budget.csv")
)

# Run analysis
df = get_variance_analysis()
dept_df = get_department_summary()
df = detect_anomalies(df)
anomaly_summary = get_anomaly_summary(df)

# Generate AI commentary
print("\n Generating AI commentary...\n")
commentary = generate_commentary(df, anomaly_summary, dept_df)
print(commentary)

# Risk flags
print("\n⚠️  Risk Flags:")
flags = generate_risk_flags(df)
for f in flags:
    print(f"  {f['period']} | {f['item']} | {f['message']}")