# 📊 FP&A AI Analyst Agent

An end-to-end financial analytics system that automates variance analysis, anomaly detection, and management commentary — transforming traditional FP&A workflows into a real-time decision system.

---

## 🚀 Live Application
🔗 https://fpa-ai-agent-garvit.streamlit.app  

## 📂 GitHub Repository
🔗 https://github.com/garvit-mittal04/fpa-ai-agent  

---

## 📌 Project Overview

Most FP&A workflows today are still:
- Manual Excel-based variance analysis  
- Static reporting with limited insight  
- Time-consuming management commentary  

This project builds an **AI-powered FP&A Analyst** that automates the entire workflow:

📊 Data Ingestion → 🧮 Variance Analysis → 🔍 Anomaly Detection → ⚠️ Risk Flags → 🤖 AI Commentary → 📥 Export Report  

---

## ⚙️ Core Features

### 📊 Variance Analysis Engine
- SQL-based aggregation of Actual vs Budget  
- FULL OUTER JOIN logic ensures **no data loss**  
- Handles real-world cases like missing actuals or budget-only entries  
- Department-level and line-item-level breakdown  

---

### 🔍 ML-Based Anomaly Detection
- Uses Isolation Forest (unsupervised ML)  
- Adaptive contamination levels based on dataset size  
- Smart gating logic avoids false positives on stable datasets  
- Identifies statistically unusual financial behavior  

---

### ⚠️ Risk Flagging System
- Flags high-impact deviations  
- Highlights business-critical risks  
- Supports decision-making for leadership  

---

### 🤖 AI-Generated Management Commentary
- Automatically generates **board-ready financial narratives**  
- Focuses on:
  - Key drivers of variance  
  - Anomalies  
  - Department-level performance  
- Designed to mimic real FP&A reporting (not generic AI text)  

---

### 📈 Interactive Dashboard (Streamlit)
- KPI Cards (Actual, Budget, Variance, Anomalies)  
- Department Summary Table  
- Variance Waterfall Chart  
- Rolling Trend Analysis  
- Anomaly Inspection Panel  
- Period-based filtering  

---

### 📥 Automated Excel Reporting
- Generates a 3-sheet report:
  1. Executive Summary  
  2. Variance Detail  
  3. AI Commentary  
- Styled and formatted for business use  

---

## 📈 Business Impact

- Reduced financial analysis time from **hours → minutes**  
- Scaled analysis across **10,000+ records**  
- Automated executive-level reporting  
- Improved anomaly detection with reduced noise  

---

## 🛠️ Tech Stack

- **Python** — Data processing & orchestration  
- **SQL (SQLite)** — Variance computation engine  
- **Scikit-learn** — ML anomaly detection (Isolation Forest)  
- **Streamlit** — Interactive UI  
- **Plotly** — Data visualization  
- **OpenPyXL** — Excel report generation  
- **LLMs** — AI-generated commentary  

---

## 🏗️ System Architecture

```
CSV Input
   ↓
SQL Engine (Variance Computation)
   ↓
ML Layer (Anomaly Detection)
   ↓
Risk Flag Generator
   ↓
AI Commentary Engine
   ↓
Streamlit Dashboard + Excel Report
```

---

## 📂 Project Structure

```
fpa-ai-agent/
│
├── app.py                  # Main Streamlit application
├── src/
│   ├── sql_engine.py       # SQL-based variance engine
│   ├── anomaly_detector.py # ML anomaly detection logic
│   ├── commentary_agent.py # AI commentary generator
│   └── report_generator.py # Excel report builder
│
├── sample_data/            # Sample datasets
├── outputs/                # Generated reports
├── requirements.txt
└── README.md
```

---

## ▶️ How to Run Locally

```bash
git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent

pip install -r requirements.txt

streamlit run app.py
```

---


## 🧠 Key Highlights

- Built to simulate **real-world FP&A workflows**, not just visualization  
- Combines **SQL + Machine Learning + AI** into one decision system  
- Handles real financial edge cases:
  - Missing actuals  
  - Budget-only entries  
  - Stable datasets with no anomalies  

---

## 🎯 Use Cases

- FP&A teams  
- Financial analysts  
- Business analysts  
- Operations & supply chain analysis  

---

## 🤝 Feedback & Contributions

Open to feedback from:
- FP&A professionals  
- Finance leaders  
- Data & analytics experts  

---

## 📬 Connect

🔗 GitHub: https://github.com/garvit-mittal04  
🔗 LinkedIn: https://www.linkedin.com/in/garvit-mittal04/
