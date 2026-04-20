from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_commentary(variance_df, anomaly_summary, dept_summary_df) -> str:
    top_unfavorable = variance_df[variance_df["variance_dollar"] < 0].head(3)
    top_favorable = variance_df[variance_df["variance_dollar"] > 0].head(3)

    unfav_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | ${r['variance_dollar']:,.0f} ({r['variance_pct']}%)"
        for _, r in top_unfavorable.iterrows()
    ])

    fav_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | ${r['variance_dollar']:,.0f} ({r['variance_pct']}%)"
        for _, r in top_favorable.iterrows()
    ])

    dept_text = "\n".join([
        f"- {r['department']}: Actual ${r['total_actual']:,.0f} vs Budget ${r['total_budget']:,.0f} (Variance: ${r['variance_dollar']:,.0f})"
        for _, r in dept_summary_df.iterrows()
    ])

    anomaly_text = ""
    if anomaly_summary["count"] > 0:
        anomaly_text = "\n".join([
            f"- {i['period']} | {i['department']} | {i['line_item']} | ${i['variance_dollar']:,.0f} ({i['variance_pct']}%)"
            for i in anomaly_summary["items"]
        ])
    else:
        anomaly_text = "No anomalies detected."

    prompt = f"""You are a senior FP&A analyst writing a monthly management commentary for the CFO and board.

DEPARTMENT SUMMARY:
{dept_text}

TOP UNFAVORABLE VARIANCES (Actual below Budget):
{unfav_text}

TOP FAVORABLE VARIANCES (Actual above Budget):
{fav_text}

ANOMALIES FLAGGED BY AI:
{anomaly_text}

Write a professional management commentary (3-4 paragraphs) that:
1. Opens with an overall performance summary vs budget
2. Explains the key drivers of major variances by department
3. Highlights the AI-flagged anomalies and why they need attention
4. Closes with a forward-looking note on what to watch next month

Tone: professional, concise, board-ready. No bullet points. Flowing paragraphs only."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    return response.choices[0].message.content


def generate_risk_flags(variance_df) -> list:
    flags = []
    high_variance = variance_df[abs(variance_df["variance_pct"]) > 10]

    for _, row in high_variance.iterrows():
        direction = "over budget" if row["variance_dollar"] > 0 else "under budget"
        dept = row["department"]
        item = row["line_item"]
        pct = abs(row["variance_pct"])
        amt = abs(row["variance_dollar"])
        flags.append({
            "item": f"{dept} — {item}",
            "period": row["period"],
            "message": f"{pct}% {direction} (${amt:,.0f})"
        })

    return flags