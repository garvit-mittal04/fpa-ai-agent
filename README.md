# 📊 FP&A AI Analyst Agent
### AI-Powered Variance Analysis & Management Commentary System

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://fpa-ai-agent-garvit.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)
[![ML](https://img.shields.io/badge/ML-Isolation%20Forest-22c55e?style=for-the-badge)](https://scikit-learn.org/)
[![Visualization](https://img.shields.io/badge/Viz-Plotly-6366F1?style=for-the-badge&logo=plotly)](https://plotly.com/python/)
[![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io/)

---

## 🚀 Live Application

🔗 **Demo:** https://fpa-ai-agent-garvit.streamlit.app  
🔗 **Repository:** https://github.com/garvit-mittal04/fpa-ai-agent

---

## 📌 Overview

FP&A teams still spend significant time on:
- manual Excel-based variance analysis
- repetitive actual vs budget review
- anomaly identification
- commentary writing for leadership
- formatting reports for distribution

This project automates that workflow end to end.

It takes uploaded **Actuals** and **Budget** CSV files, runs a **SQL-based variance engine**, applies **ML-based anomaly detection**, generates **AI management commentary**, and exports a **board-ready Excel report** through an interactive Streamlit application.

---

## 💼 Impact

- Reduced financial analysis time from **hours to minutes**
- Scaled analysis across **10,000+ records**
- Automated executive-style reporting
- Improved anomaly detection quality by reducing false positives on stable datasets

---

## 🧩 The Problem

Traditional FP&A workflows are often:
- repetitive
- slow
- spreadsheet-heavy
- hard to scale
- dependent on manual commentary quality

This creates delays in decision-making and makes reporting inconsistent across periods.

The goal of this system is to make FP&A reporting:
- faster
- more repeatable
- more explainable
- more actionable

---

## ⚙️ End-to-End Workflow

| Step | Description |
|------|-------------|
| 📥 Data Ingestion | Upload Actuals and Budget CSV files or load sample data |
| 🧮 Variance Analysis | SQL engine calculates line-item and department-level variance |
| 📈 Trend Analysis | Rolling trend logic provides historical performance context |
| 🔍 Anomaly Detection | Isolation Forest flags statistically unusual records |
| ⚠️ Risk Flagging | High-impact deviations are translated into business risk signals |
| 🤖 AI Commentary | Management commentary is generated automatically |
| 📤 Reporting | Excel report is exported for leadership distribution |

---

## ✨ Visual Highlights

Even without static screenshots, the application includes the following interface components:

- **KPI Cards** for Total Actual, Total Budget, Net Variance, and Anomalies
- **System Insight Banner** showing whether the dataset is stable or requires investigation
- **Department Summary Table** with actuals, budget, variance, and percentage deviation
- **Risk Flags Panel** for business-critical deviations
- **Variance Waterfall Chart** for top favorable and unfavorable line items
- **Trend Chart** for rolling department-level performance
- **Anomaly Table** for flagged records
- **AI Commentary Panel** with downloadable text output
- **Excel Export** for executive-ready reporting

---

## 🧠 Core Features

### 1. SQL-Based Variance Engine
- Computes actual vs budget performance using SQLite
- Supports line-item and department-level reporting
- Uses **FULL OUTER JOIN-style logic via UNION of keys** to avoid dropping budget-only or actual-only rows
- Handles real-world data mismatches more safely than a simple left join

### 2. Adaptive Anomaly Detection
- Uses **Isolation Forest** for unsupervised anomaly detection
- Applies **stability gating** so clean datasets can return zero anomalies
- Uses **adaptive contamination scaling** by dataset size
- Reduces false positives compared with fixed-threshold anomaly labeling

### 3. Risk Flag Generation
- Highlights material deviations requiring leadership attention
- Converts variance output into concise business-facing warnings
- Helps bridge the gap between analytics and action

### 4. AI-Generated Management Commentary
- Produces board-style management commentary
- Summarizes performance vs budget
- Explains department-level drivers
- Adds forward-looking context
- Includes a fallback path if the LLM service is unavailable

### 5. Interactive Streamlit Dashboard
- Fast exploratory analysis
- Period selection
- Filter-aware visuals
- Commentary export
- Excel report generation

### 6. Executive Reporting
- Generates a formatted Excel workbook with:
  - Executive Summary
  - Variance Detail
  - AI Commentary

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|------|------|---------|
| Data Processing | Pandas | CSV ingestion, cleaning, transformation |
| Query Engine | SQLite + SQLAlchemy | Variance logic and analytical queries |
| Analytics | SQL (CTEs + Window Functions) | Variance, department summaries, rolling trends |
| Machine Learning | Scikit-learn | Isolation Forest anomaly detection |
| AI Layer | Groq API / LLM | Commentary and risk narrative generation |
| Visualization | Plotly | Waterfall and trend charts |
| Reporting | openpyxl | Excel report generation |
| Frontend | Streamlit | Interactive UI and workflow orchestration |

---

## 🗄️ Core SQL Logic

```sql
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
    COALESCE(a.actual_amount, 0) - COALESCE(b.budget_amount, 0) AS variance_dollar
FROM all_keys k
LEFT JOIN actuals a
    ON k.department = a.department
   AND k.line_item = a.line_item
   AND k.period = a.period
LEFT JOIN budget b
    ON k.department = b.department
   AND k.line_item = b.line_item
   AND k.period = b.period
ORDER BY ABS(variance_dollar) DESC;
```

---

## 🔍 Anomaly Detection Logic

The anomaly engine does **not** blindly force anomalies on every dataset.

It first checks whether the uploaded data is stable using variance diagnostics. If the dataset appears stable, it returns **zero anomalies**. Otherwise, it runs Isolation Forest using adaptive contamination levels.

This makes the results more realistic and more aligned with actual finance workflows.

---

## 🏗️ System Architecture

```text
CSV Input
   ↓
Schema Validation & Standardization
   ↓
SQLite Variance Engine
   ↓
Department Summary + Trend Calculation
   ↓
ML Anomaly Detection
   ↓
Risk Flag Generation
   ↓
AI Commentary
   ↓
Streamlit Dashboard + Excel Export
```

---

## 📂 Project Structure

```text
fpa-ai-agent/
│
├── app.py
├── src/
│   ├── sql_engine.py
│   ├── anomaly_detector.py
│   ├── commentary_agent.py
│   └── report_generator.py
│
├── database/
├── sample_data/
├── outputs/
├── requirements.txt
└── README.md
```

---

## ▶️ How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your environment variable
Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_key_here
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## 📊 Sample Data Support

The application supports:
- sample actuals and budget data
- uploaded financial CSVs
- stable datasets with zero anomalies
- anomaly-heavy datasets
- budget-only and actual-only row scenarios

---

## 🎯 Use Cases

This project is relevant for:
- FP&A teams
- financial analysts
- business analysts
- analytics interns
- operations and supply chain analysts
- finance automation use cases
- management reporting workflows

---

## 📈 Why This Project Stands Out

This is not just a dashboard.

It combines:
- **data engineering**
- **SQL-based financial analytics**
- **machine learning**
- **AI-generated business communication**
- **executive reporting**

into one end-to-end decision-support workflow.

---

## 👤 Author

**Garvit Mittal**  
MS in Business Analytics & AI — The University of Texas at Dallas  
BBA (Finance) — Christ University  

🔗 **GitHub:** https://github.com/garvit-mittal04  
🔗 **LinkedIn:** https://www.linkedin.com/in/garvit-mittal04/

---

## 🤝 Feedback

Open to feedback from professionals in:
- FP&A
- Finance
- Business Analytics
- Data Science
- Operations

If you found the project interesting, a star on the repository would be appreciated.
