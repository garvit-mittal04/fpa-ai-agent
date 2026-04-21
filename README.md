# 📊 FP&A AI Analyst Agent  
### AI-Powered Variance Analysis & Management Commentary System

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://fpa-ai-agent-garvit.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)

---

## 🚀 Overview

An AI-powered FP&A decision-support system that automates:

- variance analysis  
- anomaly detection  
- risk identification  
- management commentary  
- executive reporting  

👉 Converts raw financial data into **board-ready insights in minutes**.

---

## 💡 Why this project?

Month-end close in most companies involves:

1. Exporting actuals from ERP  
2. Comparing vs budget in Excel  
3. Identifying variances manually  
4. Writing management commentary  

This process is:
- repetitive  
- time-consuming  
- inconsistent  

This system automates the entire workflow end-to-end.

> Inspired by real-world experience analyzing 20,000+ financial records and building manual variance reports.

---

## 🎯 What It Does

| Step | Capability |
|------|----------|
| 📥 Input | Upload Actuals & Budget CSVs |
| 🧮 Analysis | SQL-based variance engine |
| 📊 Trends | Rolling 3-period analysis |
| 🔍 Detection | Adaptive anomaly detection (ML + gating) |
| ⚠️ Risk | Automated risk flag generation |
| 🤖 AI | Management commentary |
| 📤 Output | Excel report + commentary export |

---

## 🧠 Key Features

### 1. End-to-End FP&A Automation
From raw CSVs → executive-ready outputs in one click.

---

### 2. SQL-Driven Variance Engine
- Uses CTEs and window functions  
- Handles multi-period financial data  
- Emulates full outer joins to avoid data loss  

---

### 3. Adaptive Anomaly Detection (Advanced)
- Isolation Forest (unsupervised ML)
- Automatic contamination tuning
- **Smart gating**: detects when dataset is stable → avoids false anomalies

👉 Makes results realistic for business use.

---

### 4. AI-Generated Commentary
Generates structured, board-ready insights:
- performance summary  
- key drivers  
- risk areas  
- forward-looking interpretation  

Includes fallback logic if LLM is unavailable.

---

### 5. Leadership Risk Flags
Flags material variances requiring attention:
- threshold-based + contextual logic  
- aligned with real FP&A workflows  

---

### 6. Executive Excel Reporting
Exports a 3-sheet model:
- Executive Summary  
- Variance Detail  
- AI Commentary  

---

## 🖥️ Screenshots

👉 *(Add actual images here for maximum impact)*

Recommended:
- Dashboard view  
- Anomaly table  
- Commentary output  
- Excel report preview  

---

## 🛠️ Tech Stack

| Layer | Tool |
|------|------|
| Data Processing | Pandas |
| Storage | SQLite + SQLAlchemy |
| Analytics | SQL (CTEs + Window Functions) |
| ML | Scikit-learn (Isolation Forest) |
| AI | Groq API (LLaMA 3) |
| Visualization | Plotly |
| Reporting | openpyxl |
| Frontend | Streamlit |

---

## 🗄️ Core SQL Example

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
    k.department,
    k.line_item,
    k.period,
    COALESCE(a.actual_amount, 0) AS actual_amount,
    COALESCE(b.budget_amount, 0) AS budget_amount,
    COALESCE(a.actual_amount, 0) - COALESCE(b.budget_amount, 0) AS variance_dollar
FROM (
    SELECT department, line_item, period FROM actuals
    UNION
    SELECT department, line_item, period FROM budget
) k
LEFT JOIN actuals a ON ...
LEFT JOIN budget b ON ...
ORDER BY ABS(variance_dollar) DESC;
