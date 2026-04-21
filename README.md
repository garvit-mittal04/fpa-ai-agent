# 📊 FP&A AI Analyst Agent

AI-powered variance analysis and financial decision support system built using Python, SQL, Machine Learning, and LLMs.

---

## 🚀 Overview

This project automates the FP&A workflow:

- Upload Actuals & Budget CSVs
- Run variance analysis using SQL
- Detect anomalies using ML
- Generate management commentary using AI
- Export executive-ready Excel reports

Designed to replicate real-world FP&A processes with production-style architecture.

---

## 🔥 Key Features

### 1. Variance Analysis (SQL Engine)
- Built using SQLite + SQLAlchemy
- Uses FULL OUTER JOIN logic (via UNION) to avoid data loss
- Handles missing actuals/budget rows correctly

### 2. Smart Anomaly Detection
- Detects if dataset is stable
- Avoids false positives on clean datasets
- Uses Isolation Forest only when required
- Adaptive contamination scaling

### 3. AI Commentary Agent
- Generates board-ready management commentary
- Identifies key drivers, risks, and insights
- Graceful fallback if API is unavailable

### 4. Risk Flags System
- Highlights departments requiring leadership attention
- Based on material variance thresholds

### 5. Excel Report Generator
Creates 3-sheet professional reports:
- Executive Summary
- Variance Detail (with anomaly highlighting)
- AI Commentary

### 6. Interactive Dashboard (Streamlit)
- KPI cards
- Variance waterfall chart
- Rolling trend analysis
- Anomaly table
- Commentary + copy button
- Download report

---

## 🧠 Tech Stack

- Python
- Pandas
- SQLite + SQLAlchemy
- Scikit-learn (Isolation Forest)
- Streamlit
- Plotly
- OpenPyXL
- Groq API (LLM)

---

## 🗂️ Project Structure

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

---

## ⚙️ Run Locally

1. Clone the repository

git clone https://github.com/garvit-mittal04/fpa-ai-agent.git
cd fpa-ai-agent

2. Install dependencies

pip install -r requirements.txt

3. Create a .env file (optional for AI commentary)

GROQ_API_KEY=your_key_here

4. Run the app

streamlit run app.py

---

## 📊 How It Works

1. Upload Actuals & Budget CSV
2. Data is validated and loaded into SQLite
3. SQL queries compute variance & trends
4. ML model detects anomalies
5. AI generates commentary
6. Dashboard displays insights
7. Excel report can be downloaded

---

## 📌 Notes

- Required CSV columns:
  department, line_item, period, amount
- Works with both clean and anomaly-heavy datasets
- Designed to avoid crashes from schema mismatches

---

## 🌐 Live App

https://fpa-ai-agent-garvit.streamlit.app

---

## 👨‍💻 Author

Garvit Mittal  
MS Business Analytics & AI @ UT Dallas

---

## ⭐ If you found this useful, consider giving a star!
