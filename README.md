# 📊 FP&A AI Analyst Agent  
### AI-Powered Variance Analysis & Management Commentary System  

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://fpa-ai-agent-garvit.streamlit.app)  
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)  
[![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)  

---

## 🚀 Overview  

An AI-powered FP&A decision-support system that automates:  

- variance analysis  
- adaptive anomaly detection  
- leadership risk flags  
- management commentary  
- executive-ready Excel reporting  

It converts uploaded Actuals and Budget data into structured financial insights through a Streamlit app powered by Python, SQL, machine learning, and LLM-based commentary generation.  

---

## 🧩 The Problem  

Month-end close in many finance teams still involves:  

1. Exporting actuals from ERP systems  
2. Comparing them against budget in spreadsheets  
3. Identifying unusual variances manually  
4. Writing management commentary for leadership  

This process is repetitive, time-consuming, and inconsistent.  

This project automates that workflow end to end.  

> Inspired by hands-on experience analyzing 20,000+ financial records and building variance reports manually at Harsiddhi Foods.  

---

## 🎯 What It Does  

| Step | What Happens |
|------|-------------|
| Data Ingestion | Upload actuals + budget CSV files or use sample data |
| SQL Variance Engine | Multi-period variance analysis using SQLite |
| Trend Analysis | Rolling 3-period trend calculation |
| Anomaly Detection | Adaptive anomaly detection with stability gating |
| Risk Flags | Leadership-oriented risk flags |
| Management Commentary | AI-generated board-ready insights |
| Excel Export | Formatted 3-sheet report |

---

## 🧠 Key Features  

### Adaptive Anomaly Detection  
Uses Isolation Forest with smart gating — avoids false anomalies on clean datasets.  

### Flexible CSV Handling  
Supports multiple dataset formats and standardizes them before processing.  

### SQL-Based Variance Analysis  
- Line-item variance  
- Department-level summary  
- Rolling trend analysis  
- Full outer join emulation (no data loss)  

### AI-Generated Commentary  
Generates structured, executive-style insights covering:  
- performance vs budget  
- key drivers  
- risk areas  
- forward-looking interpretation  

Includes fallback logic if LLM is unavailable.  

### Executive Excel Reporting  
Exports a formatted workbook with:  
- Executive Summary  
- Variance Detail  
- AI Commentary  

---

## 🖥️ Live Demo  

👉 https://fpa-ai-agent-garvit.streamlit.app  

Click **Load Sample Data → Run Analysis**  

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

## 🗄️ Core SQL Logic

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

---

## 🔍 Anomaly Detection  

- Detects if dataset is stable  
- Returns zero anomalies for clean datasets  
- Uses adaptive contamination scaling  
- Applies Isolation Forest only when needed  

---

## 📁 Project Structure  

fpa-ai-agent/
│
├── app.py
├── src/
│ ├── sql_engine.py
│ ├── anomaly_detector.py
│ ├── commentary_agent.py
│ └── report_generator.py
│
├── database/
├── sample_data/
├── outputs/
├── requirements.txt
└── .env

---

## ⚙️ Run Locally  

Clone repo:

git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent

Install dependencies:
pip install -r requirements.txt

Add `.env`:
GROQ_API_KEY=your_key_here

Run app:
streamlit run app.py

---

## 💼 Business Impact  

| Metric | Manual | This System |
|--------|--------|------------|
| Time | Hours–days | Minutes |
| Accuracy | Variable | Consistent |
| Insight | Manual | Automated |
| Scalability | Low | High |

---

## 👤 Author  

Garvit Mittal  
MS Business Analytics & AI — UT Dallas  
BBA Finance — Christ University  

LinkedIn: https://linkedin.com/in/garvit-mittal04  
GitHub: https://github.com/garvit-mittal04  
