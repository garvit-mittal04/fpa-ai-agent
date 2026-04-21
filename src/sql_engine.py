"""
sql_engine.py
-------------
SQLite database engine for the FP&A AI Agent.
Handles data ingestion, schema creation, and all analytical SQL queries.

Improvements:
- Accepts flexible CSV schemas for actuals and budget
- Supports both `amount` format and `actual_amount` / `budget_amount` format
- Normalizes column names automatically
- Produces clearer validation errors
- Keeps full outer join emulation so budget-only rows are not dropped
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "fpa_agent.db")

CANONICAL_BASE_COLUMNS = {"department", "line_item", "period"}
AMOUNT_ALIASES = {"amount", "actual_amount", "budget_amount"}

COLUMN_ALIASES = {
    "department": "department",
    "dept": "department",
    "function": "department",
    "business_unit": "department",

    "line_item": "line_item",
    "line item": "line_item",
    "lineitem": "line_item",
    "account": "line_item",
    "category": "line_item",
    "expense_category": "line_item",

    "period": "period",
    "month": "period",
    "date": "period",
    "fiscal_period": "period",

    "amount": "amount",
    "actual_amount": "actual_amount",
    "budget_amount": "budget_amount",
    "actual": "actual_amount",
    "budget": "budget_amount",
}


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


def normalize_column_name(col: str) -> str:
    """Normalize raw column names."""
    col = col.strip().lower()
    col = col.replace("-", "_")
    col = col.replace(" ", "_")
    return COLUMN_ALIASES.get(col, col)


def normalize_period(series: pd.Series) -> pd.Series:
    """
    Normalize period values into YYYY-MM where possible.
    Falls back to stripped string if parsing fails.
    """
    parsed = pd.to_datetime(series, errors="coerce")
    normalized = parsed.dt.strftime("%Y-%m")

    original = series.astype(str).str.strip()
    return normalized.fillna(original)


def normalize_text(series: pd.Series) -> pd.Series:
    """Trim and standardize text values."""
    return series.astype(str).str.strip()


def normalize_amount(series: pd.Series, col_name: str) -> pd.Series:
    """Convert amount column to numeric with clear error if invalid."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().all():
        raise ValueError(
            f"Column '{col_name}' could not be interpreted as numeric. "
            f"Please check the uploaded file."
        )
    return numeric.fillna(0.0)


def standardize_dataframe(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """
    Standardize a raw uploaded dataframe into canonical column names.
    Supports:
    - actuals with amount or actual_amount
    - budget with amount or budget_amount
    """
    if df is None or df.empty:
        raise ValueError(f"{label} CSV is empty.")

    out = df.copy()
    out.columns = [normalize_column_name(c) for c in out.columns]

    found_cols = set(out.columns)

    missing_base = CANONICAL_BASE_COLUMNS - found_cols
    if missing_base:
        raise ValueError(
            f"{label} CSV is missing required columns: {missing_base}. "
            f"Found columns: {sorted(found_cols)}"
        )

    # Resolve amount column
    if label.lower() == "actuals":
        if "actual_amount" in out.columns:
            out["amount"] = out["actual_amount"]
        elif "amount" in out.columns:
            out["amount"] = out["amount"]
        else:
            raise ValueError(
                f"{label} CSV must contain either 'amount' or 'actual_amount'. "
                f"Found columns: {sorted(found_cols)}"
            )

    elif label.lower() == "budget":
        if "budget_amount" in out.columns:
            out["amount"] = out["budget_amount"]
        elif "amount" in out.columns:
            out["amount"] = out["amount"]
        else:
            raise ValueError(
                f"{label} CSV must contain either 'amount' or 'budget_amount'. "
                f"Found columns: {sorted(found_cols)}"
            )
    else:
        if "amount" not in out.columns:
            raise ValueError(
                f"{label} CSV must contain an amount-like column. "
                f"Found columns: {sorted(found_cols)}"
            )

    # Keep only canonical columns
    out = out[["department", "line_item", "period", "amount"]].copy()

    # Normalize data types
    out["department"] = normalize_text(out["department"])
    out["line_item"] = normalize_text(out["line_item"])
    out["period"] = normalize_period(out["period"])
    out["amount"] = normalize_amount(out["amount"], "amount")

    # Drop blank keys
    out = out[
        (out["department"] != "") &
        (out["line_item"] != "") &
        (out["period"] != "")
    ].copy()

    if out.empty:
        raise ValueError(f"{label} CSV contains no usable rows after cleaning.")

    return out


def validate_schema(df: pd.DataFrame, label: str):
    """
    Validate after normalization.
    Raises ValueError with a clear message if required columns are missing.
    """
    cols = {c.lower().strip() for c in df.columns}
    required = {"department", "line_item", "period", "amount"}
    missing = required - cols
    if missing:
        raise ValueError(
            f"{label} CSV is missing required columns after normalization: {missing}. "
            f"Expected: {required}. Found: {cols}"
        )


def load_csv_to_db(actuals_df: pd.DataFrame, budget_df: pd.DataFrame):
    """
    Standardize, validate, then load actuals and budget DataFrames into SQLite.
    Supports multiple input schemas.
    """
    actuals = standardize_dataframe(actuals_df, "Actuals")
    budget = standardize_dataframe(budget_df, "Budget")

    validate_schema(actuals, "Actuals")
    validate_schema(budget, "Budget")

    engine = get_engine()
    init_db()

    actuals["data_type"] = "actual"
    budget["data_type"] = "budget"

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
            COALESCE(a.actual_amount, 0) AS actual_amount,
            COALESCE(b.budget_amount, 0) AS budget_amount,
            COALESCE(a.actual_amount, 0) - COALESCE(b.budget_amount, 0) AS variance_dollar,
            ROUND(
                (COALESCE(a.actual_amount, 0) - COALESCE(b.budget_amount, 0))
                / NULLIF(COALESCE(b.budget_amount, 0), 0) * 100,
            2) AS variance_pct
        FROM all_keys k
        LEFT JOIN actuals a
            ON  k.department = a.department
            AND k.line_item = a.line_item
            AND k.period = a.period
        LEFT JOIN budget b
            ON  k.department = b.department
            AND k.line_item = b.line_item
            AND k.period = b.period
        ORDER BY ABS(variance_dollar) DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_department_summary() -> pd.DataFrame:
    """
    Aggregate actual vs budget totals by department.

    Uses UNION-based full outer join emulation so budget-only departments
    are not lost.
    """
    engine = get_engine()
    query = text("""
        WITH actuals AS (
            SELECT department, SUM(amount) AS total_actual
            FROM financial_data WHERE data_type = 'actual'
            GROUP BY department
        ),
        budget AS (
            SELECT department, SUM(amount) AS total_budget
            FROM financial_data WHERE data_type = 'budget'
            GROUP BY department
        ),
        all_depts AS (
            SELECT department FROM actuals
            UNION
            SELECT department FROM budget
        )
        SELECT
            d.department,
            ROUND(COALESCE(a.total_actual, 0), 2) AS total_actual,
            ROUND(COALESCE(b.total_budget, 0), 2) AS total_budget,
            ROUND(COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0), 2) AS variance_dollar,
            ROUND(
                (COALESCE(a.total_actual, 0) - COALESCE(b.total_budget, 0))
                / NULLIF(COALESCE(b.total_budget, 0), 0) * 100, 2
            ) AS variance_pct
        FROM all_depts d
        LEFT JOIN actuals a ON d.department = a.department
        LEFT JOIN budget b ON d.department = b.department
        ORDER BY ABS(variance_dollar) DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def get_rolling_trends() -> pd.DataFrame:
    """Rolling 3-month average of actuals per department/line item via window function."""
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
