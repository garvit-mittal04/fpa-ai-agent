import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "fpa_agent.db")

def get_engine():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH}")

def init_db():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS financial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                department TEXT NOT NULL,
                line_item TEXT NOT NULL,
                amount REAL NOT NULL,
                data_type TEXT NOT NULL
            )
        """))
        conn.commit()

def load_csv_to_db(actuals_path, budget_path):
    engine = get_engine()
    init_db()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM financial_data"))
        conn.commit()

    actuals_df = pd.read_csv(actuals_path)
    actuals_df["data_type"] = "actual"
    budget_df = pd.read_csv(budget_path)
    budget_df["data_type"] = "budget"
    combined = pd.concat([actuals_df, budget_df], ignore_index=True)
    combined.to_sql("financial_data", get_engine(), if_exists="append", index=False)
    print("Data loaded successfully!")

def get_variance_analysis():
    engine = get_engine()
    query = """
        WITH actuals AS (
            SELECT department, line_item, period, SUM(amount) AS actual_amount
            FROM financial_data WHERE data_type = 'actual'
            GROUP BY department, line_item, period
        ),
        budget AS (
            SELECT department, line_item, period, SUM(amount) AS budget_amount
            FROM financial_data WHERE data_type = 'budget'
            GROUP BY department, line_item, period
        )
        SELECT
            a.period,
            a.department,
            a.line_item,
            a.actual_amount,
            b.budget_amount,
            (a.actual_amount - b.budget_amount) AS variance_dollar,
            ROUND((a.actual_amount - b.budget_amount) / NULLIF(b.budget_amount, 0) * 100, 2) AS variance_pct
        FROM actuals a
        LEFT JOIN budget b
            ON a.department = b.department
            AND a.line_item = b.line_item
            AND a.period = b.period
        ORDER BY ABS(a.actual_amount - b.budget_amount) DESC
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

def get_rolling_trends():
    engine = get_engine()
    query = """
        SELECT
            department,
            line_item,
            period,
            SUM(amount) AS actual_amount,
            AVG(SUM(amount)) OVER (
                PARTITION BY department, line_item
                ORDER BY period
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS rolling_3m_avg
        FROM financial_data
        WHERE data_type = 'actual'
        GROUP BY department, line_item, period
        ORDER BY department, line_item, period
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

def get_department_summary():
    engine = get_engine()
    query = """
        WITH actuals AS (
            SELECT department, SUM(amount) AS total_actual
            FROM financial_data WHERE data_type = 'actual'
            GROUP BY department
        ),
        budget AS (
            SELECT department, SUM(amount) AS total_budget
            FROM financial_data WHERE data_type = 'budget'
            GROUP BY department
        )
        SELECT
            a.department,
            a.total_actual,
            b.total_budget,
            (a.total_actual - b.total_budget) AS variance_dollar,
            ROUND((a.total_actual - b.total_budget) / NULLIF(b.total_budget, 0) * 100, 2) AS variance_pct
        FROM actuals a
        LEFT JOIN budget b ON a.department = b.department
        ORDER BY ABS(a.total_actual - b.total_budget) DESC
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)