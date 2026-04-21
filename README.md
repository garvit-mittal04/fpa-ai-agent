# 📊 FP&A AI Analyst Agent
### AI-Powered Variance Analysis & Management Commentary System

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://fpa-ai-agent-garvit.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)
[![ML](https://img.shields.io/badge/ML-IsolationForest-22c55e?style=for-the-badge)]

---

## 🚀 Overview

An AI-powered FP&A system that automates:

- 📊 Variance Analysis  
- 🔍 Anomaly Detection  
- ⚠️ Risk Flagging  
- 🤖 Management Commentary  
- 📥 Excel Reports  

Converts financial data into **board-ready insights in minutes**.
---

## 💼 Impact

- Reduced FP&A variance analysis time from hours to minutes  
- Scaled anomaly detection across 10,000+ financial records  
- Automated generation of executive-ready management commentary  

---

## 🧠 Problem

FP&A workflows are:
- Manual
- Time-consuming
- Inconsistent

This project automates the entire pipeline.

---

## ⚙️ System Flow

| Step | Description |
|------|------------|
| 📥 Input | Upload Actuals & Budget CSV |
| 🧮 SQL | Variance Analysis |
| 📈 Trends | Rolling Analysis |
| 🔍 ML | Anomaly Detection |
| ⚠️ Risk | Flags |
| 🤖 AI | Commentary |
| 📤 Output | Excel + Dashboard |

---

## 🖥️ Live App

https://fpa-ai-agent-garvit.streamlit.app

---

## 🧠 Key Features

### 🔍 Adaptive Anomaly Detection
- Detects stable datasets
- Avoids false positives
- Uses ML only when needed

### 🧮 SQL Engine
- CTE-based queries
- FULL OUTER JOIN logic (via UNION)
- No data loss

### 🤖 AI Commentary
- Executive-level insights
- Risk & driver explanation
- Fallback safe mode

### 📊 Dashboard
- KPI Cards
- Waterfall Chart
- Trends
- Anomaly View

### 📥 Excel Export
- Executive Summary
- Variance Detail
- AI Commentary

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

## 🛠️ Tech Stack

| Layer | Tool |
|------|------|
| Data | Pandas |
| DB | SQLite |
| ML | Scikit-learn |
| AI | Groq API |
| Viz | Plotly |
| UI | Streamlit |

---

## 📁 Project Structure

```
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
└── .env
```

---

## ⚙️ Run Locally

### 1. Clone
```bash
git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent
```

### 2. Install
```bash
pip install -r requirements.txt
```

### 3. Setup .env
```
GROQ_API_KEY=your_key_here
```

### 4. Run
```bash
streamlit run app.py
```

---

## 💼 Business Impact

| Metric | Manual | System |
|--------|--------|--------|
| Time | Hours | Minutes |
| Accuracy | Variable | Consistent |
| Insight | Manual | Automated |

---

## 👤 Author

Garvit Mittal  
MS Business Analytics & AI — UT Dallas  

LinkedIn: https://linkedin.com/in/garvit-mittal04  
GitHub: https://github.com/garvit-mittal04  

---

⭐ If you found this useful, consider starring the repo!
