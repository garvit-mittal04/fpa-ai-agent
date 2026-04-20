
# 📊 FP&A AI Analyst Agent
### Automated Variance Analysis & Management Commentary Generator

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://fpa-ai-agent-garvit.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)

---

## 🧩 The Problem

Every company's finance team does the same thing every month-end close:

1. Someone exports actuals from the ERP into Excel
2. They manually compare each line item against the budget
3. They write a management commentary explaining the gaps
4. They send it to leadership — usually 2 to 5 days after close

This process is **repetitive, error-prone, and entirely automatable**. A single analyst can spend days just on formatting, copy-pasting, and writing narratives that follow the same structure every month.

This project is the AI-powered version of that workflow. It takes the same actuals vs. budget data and produces a complete variance analysis, anomaly report, and board-ready management commentary — **in under 2 minutes**.

> **Real-world context:** This project was inspired by hands-on experience analyzing 20,000+ financial records and building variance reports manually at Harsiddhi Foods. The inefficiency of that process was the motivation for automating it.

---

## 🚀 Live Demo

👉 **[fpa-ai-agent-garvit.streamlit.app](https://fpa-ai-agent-garvit.streamlit.app)**

Click **"Load Sample Data"** in the sidebar, then **"▶ Run Analysis"** to see the full pipeline in action — no login or setup required.

### 📹 Video Walkthrough

https://github.com/user-attachments/assets/cf07c76a-6ed6-49b3-8ba6-f2966673a34e

---

## 🎯 What It Does

The agent mimics what an FP&A analyst does every month-end close:

| Step | What Happens |
|------|-------------|
| **1. Data Ingestion** | Upload actuals + budget CSV files (or use sample data) |
| **2. SQL Variance Engine** | Multi-period variance analysis using CTEs and window functions in SQLite |
| **3. Statistical Analysis** | Rolling 3-month trend calculation per department and line item |
| **4. Anomaly Detection** | Isolation Forest (Scikit-learn) flags statistical outliers automatically |
| **5. AI Risk Flags** | LLM identifies items with >10% variance and generates concise risk flags |
| **6. Management Commentary** | GPT-quality narrative commentary generated via Groq (llama-3.1-8b-instant) |
| **7. Excel Export** | Formatted 3-sheet Excel report ready for distribution |

---

## 🖥️ App Screenshots

### Dashboard Overview
- **KPI Cards** — Total Actual, Total Budget, Net Variance $, Anomalies Detected
- **Department Summary** — 6 departments with actual vs. budget comparison
- **Risk Flags** — LLM-generated flags for items significantly off budget

### Charts
- **Variance Waterfall** — Top 10 favorable/unfavorable line items (green/red)
- **Rolling Trend Chart** — 3-month moving average per department over 12 periods

### AI Outputs
- **Anomaly Table** — 41 flagged line items highlighted in red
- **Management Commentary** — 3-4 paragraph board-ready narrative
- **Excel Download** — Executive Summary, Variance Detail, and AI Commentary sheets

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Data Ingestion** | Python (Pandas) | Parse and validate uploaded CSV files |
| **Storage & Querying** | SQLite + SQLAlchemy | Store multi-period data, run variance CTEs |
| **Variance Analysis** | SQL (CTEs + Window Functions) | Period-over-period variance, rolling averages |
| **Anomaly Detection** | Scikit-learn (Isolation Forest) | Flag statistical outliers in financial data |
| **AI Commentary** | Groq API (llama-3.1-8b-instant) | Generate management commentary and risk flags |
| **Visualization** | Plotly | Interactive waterfall and trend charts |
| **Excel Output** | openpyxl | Formatted variance model with 3 sheets |
| **Frontend** | Streamlit | Web UI, file upload, live dashboard |
| **Deployment** | Streamlit Community Cloud | Free live URL from GitHub |

---

## 🗄️ Core SQL — Variance CTE

The engine uses a Common Table Expression to join actuals against budget and compute dollar and percentage variance, ordered by the largest gaps:

```sql
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
    ON a.department = b.department
   AND a.line_item  = b.line_item
   AND a.period     = b.period
ORDER BY ABS(variance_dollar) DESC;
```

A second query uses a **window function** to compute the rolling 3-month average per department and line item:

```sql
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
FROM actuals_view
ORDER BY department, line_item, period;
```

---

## 🤖 AI Commentary — How It Works

The commentary agent builds a structured prompt from the variance summary and passes it to the LLM:

```python
def generate_commentary(variance_df, anomaly_summary, dept_summary_df):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Extract top movers and department performance
    # Build structured prompt with financial context
    # Return 3-4 paragraph board-ready narrative
```

The prompt includes total variance, top 3 favorable and unfavorable line items, department-level performance, and anomaly count — giving the model enough context to write a commentary that reads like a senior analyst wrote it.

---

## 🔍 Anomaly Detection — Isolation Forest

The agent uses Scikit-learn's Isolation Forest to detect statistically unusual line items without needing labeled training data:

```python
from sklearn.ensemble import IsolationForest

features = ["actual_amount", "budget_amount", "variance_dollar", "variance_pct"]
model = IsolationForest(contamination=0.1, random_state=42)
df["anomaly_score"] = model.fit_predict(df[features])
df["is_anomaly"] = df["anomaly_score"] == -1
```

Items flagged as anomalies are highlighted in red in the variance table and included in the management commentary context.

---

## 📁 Project Structure

```
fpa-ai-agent/
│
├── app.py                       # Streamlit entry point
│
├── src/
│   ├── sql_engine.py            # SQLite connection + variance queries
│   ├── anomaly_detector.py      # Isolation Forest outlier detection
│   ├── commentary_agent.py      # Groq API + prompt engineering
│   └── report_generator.py      # openpyxl Excel export
│
├── database/
│   └── schema.sql               # Table definitions
│
├── sample_data/
│   ├── actual.csv               # 408 rows — 12 months, 6 departments
│   └── budget.csv               # 408 rows — matching budget data
│
├── outputs/                     # Generated Excel reports
├── requirements.txt
└── .env                         # API keys (not committed)
```

---

## 📦 Sample Dataset

The sample data contains **408 rows** of realistic financial data:

- **12 months** — January 2023 to December 2023
- **6 departments** — Sales, Marketing, Operations, Finance, HR, R&D
- **32 line items** — Revenue streams, COGS, operating expenses, payroll
- **Built-in patterns** — Q4 logistics cost spike, marketing overspend, seasonal revenue variation
- **41 anomalies** — Statistically unusual line items detectable by the ML model

---

## ⚙️ Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your API key
Create a `.env` file in the root directory:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free API key at [console.groq.com](https://console.groq.com) — no credit card required.

### 4. Run the app
```bash
streamlit run app.py
```

---

## 📋 Requirements

```
streamlit
pandas
sqlalchemy
scikit-learn
plotly
openpyxl
groq
python-dotenv
```

---

## 💼 Business Impact

| Metric | Manual Process | This Agent |
|--------|---------------|------------|
| Time to complete variance analysis | 2–5 days | < 2 minutes |
| Anomalies caught | Depends on analyst | 100% of statistical outliers |
| Commentary consistency | Varies by author | Consistent, structured, board-ready |
| Cost | Analyst time ($) | Free (Groq API, Streamlit Cloud) |

---

## 👤 Author

**Garvit Mittal**
MS Business Analytics & AI — UT Dallas
BBA Finance Hons. — Christ University

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/garvit-mittal04)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/garvit-mittal04)
