import pymysql
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def get_engine():
    from urllib.parse import quote_plus
    user = os.getenv("DB_USER")
    password = quote_plus(os.getenv("DB_PASSWORD"))
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}")

def load_csv_to_db(actuals_path, budget_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM financial_data")

    actuals_df = pd.read_csv(actuals_path)
    actuals_df["data_type"] = "actual"

    budget_df = pd.read_csv(budget_path)
    budget_df["data_type"] = "budget"

    combined = pd.concat([actuals_df, budget_df], ignore_index=True)

    for _, row in combined.iterrows():
        cursor.execute("""
            INSERT INTO financial_data (period, department, line_item, amount, data_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (row["period"], row["department"], row["line_item"], row["amount"], row["data_type"]))

    conn.commit()
    cursor.close()
    conn.close()
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
        df = pd.read_sql(text(query), conn)
    return df

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
        df = pd.read_sql(text(query), conn)
    return df

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
        df = pd.read_sql(text(query), conn)
    return df