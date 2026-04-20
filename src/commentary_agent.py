import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def generate_commentary(variance_df, anomaly_summary, dept_summary_df) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    top_unfavorable = variance_df[variance_df["variance_dollar"] < 0].head(3)
    top_favorable = variance_df[variance_df["variance_dollar"] > 0].head(3)

    unfav_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | ${r['variance_dollar']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in top_unfavorable.iterrows()
    ])

    fav_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | ${r['variance_dollar']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in top_favorable.iterrows()
    ])

    dept_text = "\n".join([
        f"- {r['department']}: Actual ${r['total_actual']:,.0f} vs Budget ${r['total_budget']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in dept_summary_df.iterrows()
    ])

    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    anomaly_count = anomaly_summary.get("total_anomalies", 0)
    anomaly_depts = anomaly_summary.get("departments_affected", [])

    prompt = f"""
You are a senior FP&A analyst writing a management commentary for the monthly close.

Overall Performance:
- Total Actual: ${total_actual:,.0f}
- Total Budget: ${total_budget:,.0f}
- Net Variance: ${total_var:,.0f} ({total_var_pct:+.1f}%)

Department Summary:
{dept_text}

Top 3 Unfavorable Variances:
{unfav_text}

Top 3 Favorable Variances:
{fav_text}

Anomalies Detected: {anomaly_count} line items flagged across departments: {', '.join(anomaly_depts) if anomaly_depts else 'None'}

Write a concise management commentary (3-4 paragraphs) that:
1. Summarizes overall financial performance vs budget
2. Explains the key drivers of major variances by department
3. Flags any items requiring leadership attention
4. Provides forward-looking context for next month

Tone: professional, direct, board-ready. Avoid jargon. Do not use bullet points.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    return response.choices[0].message.content


def generate_risk_flags(variance_df) -> list:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    high_variance = variance_df[abs(variance_df["variance_pct"]) > 10].copy()
    high_variance = high_variance.sort_values("variance_pct", key=abs, ascending=False).head(10)

    if high_variance.empty:
        return ["No significant risk flags detected."]

    items_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | ${r['variance_dollar']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in high_variance.iterrows()
    ])

    prompt = f"""
You are a senior FP&A analyst. Based on these high-variance line items (>10% off budget), 
generate 3-5 concise risk flags for leadership. Each flag should be one sentence.

High Variance Items:
{items_text}

Format each risk flag as a single sentence starting with the department name.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512
    )

    raw = response.choices[0].message.content
    flags = [line.strip("- ").strip() for line in raw.strip().split("\n") if line.strip()]
    return flags