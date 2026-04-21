# 📊 FP&A AI Analyst Agent

An end-to-end financial analytics system that automates variance analysis, anomaly detection, and management commentary — transforming traditional FP&A workflows into real-time decision systems.

---

## 🚀 Live Application
https://fpa-ai-agent-garvit.streamlit.app  

---

## 📌 Project Overview

Most FP&A workflows today still rely on:
- Manual Excel-based variance analysis  
- Static reports with limited insight  
- Time-consuming commentary writing  

This project builds an AI-powered FP&A analyst that automates the full workflow:

Data → Variance → Anomalies → Risks → Commentary → Report

---

## ⚙️ Core Features

### Variance Engine
- SQL-based Actual vs Budget comparison  
- FULL OUTER JOIN logic (no data loss)  
- Department & line-item analysis  

### Anomaly Detection
- Isolation Forest (ML)  
- Adaptive sensitivity  
- No false positives on stable datasets  

### Risk Flags
- Highlights high-impact deviations  

### AI Commentary
- Board-ready financial insights  
- Focused, structured, non-generic  

### Dashboard
- KPI cards  
- Department table  
- Waterfall chart  
- Trend analysis  
- Anomaly table  

### Export
- Excel report with summary + details + commentary  

---

## 📈 Impact

- Hours → Minutes (analysis time)  
- 10,000+ records handled  
- Automated reporting  

---

## 🛠️ Tech Stack

Python, SQL, Streamlit, Scikit-learn, Plotly, OpenPyXL, LLMs

---

## 🏗️ Architecture

CSV → SQL → ML → Risk → AI → Dashboard

---

## ▶️ Run Locally

```bash
git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent
pip install -r requirements.txt
streamlit run app.py
```

---

## 📂 Structure

```
app.py
src/
  sql_engine.py
  anomaly_detector.py
  commentary_agent.py
  report_generator.py
sample_data/
outputs/
```

---

## 🤝 Feedback

Open to feedback from FP&A, finance, and analytics professionals.
