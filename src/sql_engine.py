"""
sql_engine.py
-------------
SQLite database engine for the FP&A AI Agent.
Handles data ingestion, schema creation, and all analytical SQL queries.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

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
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                department  TEXT,
                line_item   TEXT,
                period      TEXT,
                amount      REAL,
                data_type   TEXT
            )
        """))
        conn.commit()


def load_csv_to_db(actuals_df: pd.DataFrame, budget_df: pd.DataFrame):
    """Load actuals and budget DataFrames into SQLite."""
    engine = get_engine()
    init_db()

    actuals = actuals_df.copy()
    budget = budget_df.copy()

    actuals["data_type"] = "actual"
    budget["data_type"] = "budget"

    combined = pd.concat([actuals, budget], ignore_index=True)
    combined.columns = [c.lower().strip() for c in combined.columns]

    combined.to_sql("financial_data", engine, if_exists="replace", index=False)
    print("Data loaded successfully!")


def get_variance_analysis() -> pd.DataFrame:
    """
    Compute period-level variance using a CTE.
    Returns actuals, budget, variance $ and % per department / line item / period,
    ordered by absolute variance descending.
    """
    engine = get_engine()
    query = text("""
        WITH actuals AS (
            SELECT department, line_item, period, SUM(amount) AS actual_amount
            FROM financial_data
            WHERE data_type = 'actual'
            GROUP BY department, line_item, period
        ),
        budget AS (
            SELECT department, line_item, period, SUM(amount) AS budget_amount
            FROM financial_data
            WHERE data_type = 'budget'
            GROUP BY department, line_item, period
        )
        SELECT
            a.department,
            a.line_item,
            a.period,
            a.actual_amount,
            b.budget_amount,
            (a.actual_amount - b.budget_amount)                              AS variance_dollar,
            ROUND((a.actual_amount - b.budget_amount)
                / NULLIF(b.budget_amount, 0) * 100, 2)                      AS variance_pct
        FROM actuals a
        LEFT JOIN budget b
            ON  a.department = b.department
            AND a.line_item  = b.line_item
            AND a.period     = b.period
        ORDER BY ABS(variance_dollar) DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_department_summary() -> pd.DataFrame:
    """
    Aggregate actual vs budget by department.
    Returns total_actual, total_budget, variance_dollar, variance_pct per department.
    """
    engine = get_engine()
    query = text("""
        WITH actuals AS (
            SELECT department, SUM(amount) AS total_actual
            FROM financial_data
            WHERE data_type = 'actual'
            GROUP BY department
        ),
        budget AS (
            SELECT department, SUM(amount) AS total_budget
            FROM financial_data
            WHERE data_type = 'budget'
            GROUP BY department
        )
        SELECT
            a.department,
            ROUND(a.total_actual, 2)  AS total_actual,
            ROUND(b.total_budget, 2)  AS total_budget,
            ROUND(a.total_actual - b.total_budget, 2) AS variance_dollar,
            ROUND((a.total_actual - b.total_budget)
                / NULLIF(b.total_budget, 0) * 100, 2)  AS variance_pct
        FROM actuals a
        LEFT JOIN budget b ON a.department = b.department
        ORDER BY ABS(variance_dollar) DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_rolling_trends() -> pd.DataFrame:
    """
    Compute rolling 3-month average of actuals per department and line item
    using a SQL window function.
    """
    engine = get_engine()
    query = text("""
        WITH actuals_agg AS (
            SELECT department, line_item, period, SUM(amount) AS actual_amount
            FROM financial_data
            WHERE data_type = 'actual'
            GROUP BY department, line_item, period
        )
        SELECT
            department,
            line_item,
            period,
            actual_amount,
            AVG(actual_amount) OVER (
                PARTITION BY department, line_item
                ORDER BY period
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS rolling_3m_avg
        FROM actuals_agg
        ORDER BY department, line_item, period
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
