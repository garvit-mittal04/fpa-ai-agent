"""
sql_engine.py
-------------
SQLite database engine for the FP&A AI Agent.
Handles data ingestion, schema creation, and all analytical SQL queries.

Fix: variance query uses FULL OUTER JOIN emulation (LEFT JOIN + UNION)
so budget-only rows are not silently dropped.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "fpa_agent.db")

REQUIRED_COLUMNS = {"department", "line_item", "period", "amount"}


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


def validate_schema(df: pd.DataFrame, label: str):
    """Raise ValueError with a clear message if required columns are missing."""
    cols   = {c.lower().strip() for c in df.columns}
    missing = REQUIRED_COLUMNS - cols
    if missing:
        raise ValueError(
            f"{label} CSV is Missing required columns: {missing}. "
            f"Expected: {REQUIRED_COLUMNS}. Found: {cols}"
        )


def load_csv_to_db(actuals_df: pd.DataFrame, budget_df: pd.DataFrame):
    """
    Validate schema then load actuals and budget DataFrames into SQLite.
    Raises ValueError with a clear message if columns are missing.
    """
    validate_schema(actuals_df, "Actuals")
    validate_schema(budget_df,  "Budget")

    engine = get_engine()
    init_db()

    actuals = actuals_df.copy()
    budget  = budget_df.copy()

    actuals.columns = [c.lower().strip() for c in actuals.columns]
    budget.columns  = [c.lower().strip() for c in budget.columns]

    actuals["data_type"] = "actual"
    budget["data_type"]  = "budget"

    combined = pd.concat([actuals, budget], ignore_index=True)
    combined.to_sql("financial_data", engine, if_exists="replace", index=False)
    print("Data loaded successfully!")


def get_variance_analysis() -> pd.DataFrame:
    """
    Compute period-level variance.

    Uses UNION-based full outer join emulation so budget-only rows
    (lines that exist in budget but have no actuals) are not lost.
    Ordered by absolute variance descending.
    """
    engine = get_engine()
    query  = text("""
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
        ),
        all_keys AS (
            SELECT department, line_item, period FROM actuals
            UNION
            SELECT department, line_item, period FROM budget
        )
        SELECT
            k.department,
            k.line_item,
            k.period,
            COALESCE(a.actual_amount, 0)                                     AS actual_amount,
            COALESCE(b.budget_amount, 0)                                     AS budget_amount,
            COALESCE(a.actual_amount, 0) - COALESCE(b.budget_amount, 0)      AS variance_dollar,
            ROUND(
                (COALESCE(a.actual_amount, 0) - COALESCE(b.budget_amount, 0))
                / NULLIF(COALESCE(b.budget_amount, 0), 0) * 100,
            2)                                                               AS variance_pct
        FROM all_keys k
        LEFT JOIN actuals a
            ON  k.department = a.department
            AND k.line_item  = a.line_item
            AND k.period     = a.period
        LEFT JOIN budget b
            ON  k.department = b.department
            AND k.line_item  = b.line_item
            AND k.period     = b.period
        ORDER BY ABS(variance_dollar) DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_department_summary() -> pd.DataFrame:
    """Aggregate actual vs budget totals by department."""
    engine = get_engine()
    query  = text("""
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
            ROUND(a.total_actual, 2)                                          AS total_actual,
            ROUND(b.total_budget, 2)                                          AS total_budget,
            ROUND(a.total_actual - b.total_budget, 2)                         AS variance_dollar,
            ROUND((a.total_actual - b.total_budget)
                / NULLIF(b.total_budget, 0) * 100, 2)                        AS variance_pct
        FROM actuals a
        LEFT JOIN budget b ON a.department = b.department
        ORDER BY ABS(variance_dollar) DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_rolling_trends() -> pd.DataFrame:
    """Rolling 3-month average of actuals per department/line item via window function."""
    engine = get_engine()
    query  = text("""
        WITH actuals_agg AS (
            SELECT department, line_item, period, SUM(amount) AS actual_amount
            FROM financial_data WHERE data_type = 'actual'
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