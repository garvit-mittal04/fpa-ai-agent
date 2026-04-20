"""
commentary_agent.py
-------------------
Generates board-ready management commentary and risk flags using the Groq API.

Commentary quality is judged by:
  - Does it correctly identify the top favorable/unfavorable variances?
  - Does it mention the departments with the largest gaps?
  - Is the tone professional and concise (3-4 paragraphs)?
  - Does it flag items that need leadership attention?

Fallback behaviour:
  - If GROQ_API_KEY is missing  → EnvironmentError caught, UI shows warning
  - If API call fails            → Exception caught, rule-based fallback returned
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> Groq:
    """Initialise Groq client at call time so env vars are always fresh."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file or Streamlit secrets."
        )
    return Groq(api_key=api_key)


def generate_commentary(variance_df, anomaly_summary: dict, dept_summary_df) -> str:
    """
    Generate 3-4 paragraph board-ready management commentary.

    Returns a fallback message string (never raises) so the UI always gets
    something displayable even when the API is unavailable.
    """
    try:
        client = _get_client()
    except EnvironmentError as e:
        return f"⚠️ Commentary unavailable: {e}"

    top_unfavorable = variance_df[variance_df["variance_dollar"] < 0].head(3)
    top_favorable   = variance_df[variance_df["variance_dollar"] > 0].head(3)

    unfav_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | "
        f"${r['variance_dollar']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in top_unfavorable.iterrows()
    ])

    fav_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | "
        f"${r['variance_dollar']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in top_favorable.iterrows()
    ])

    dept_text = "\n".join([
        f"- {r.iloc[0]}: Actual ${r.iloc[1]:,.0f} vs Budget "
        f"${r.iloc[2]:,.0f} ({r.iloc[4]:+.1f}%)"
        for _, r in dept_summary_df.iterrows()
    ])

    total_actual  = variance_df["actual_amount"].sum()
    total_budget  = variance_df["budget_amount"].sum()
    total_var     = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    # Use stable contract keys from get_anomaly_summary()
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

Anomalies Detected: {anomaly_count} line items flagged across departments: \
{', '.join(anomaly_depts) if anomaly_depts else 'None'}

Write a concise management commentary (3-4 paragraphs) that:
1. Summarizes overall financial performance vs budget
2. Explains the key drivers of major variances by department
3. Flags any items requiring leadership attention
4. Provides forward-looking context for next month

Tone: professional, direct, board-ready. Avoid jargon. Do not use bullet points.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return (
            "⚠️ Commentary generation failed. Please check your API key and try again.\n"
            f"Error: {e}"
        )


def generate_risk_flags(variance_df) -> list:
    """
    Generate 3-5 concise risk flag strings for items >10% off budget.

    Always returns a list of strings — falls back to rule-based logic
    if the API is unavailable, so the UI never shows an empty section.
    """
    high_variance = variance_df[abs(variance_df["variance_pct"]) > 10].copy()
    high_variance = high_variance.reindex(
        high_variance["variance_pct"].abs().sort_values(ascending=False).index
    ).head(10)

    if high_variance.empty:
        return ["No significant risk flags detected — all line items within 10% of budget."]

    try:
        client = _get_client()
    except EnvironmentError:
        return _rule_based_flags(high_variance)

    items_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | "
        f"${r['variance_dollar']:,.0f} ({r['variance_pct']:+.1f}%)"
        for _, r in high_variance.iterrows()
    ])

    prompt = f"""
You are a senior FP&A analyst. Based on these high-variance line items (>10% off budget),
generate 3-5 concise risk flags for leadership. Each flag must be one sentence.

High Variance Items:
{items_text}

Format each risk flag as a single sentence starting with the department name.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        raw   = response.choices[0].message.content
        flags = [ln.strip("- •").strip() for ln in raw.strip().split("\n") if ln.strip()]
        return flags if flags else _rule_based_flags(high_variance)
    except Exception:
        return _rule_based_flags(high_variance)


def _rule_based_flags(high_variance) -> list:
    """Rule-based fallback — no API required."""
    flags = []
    for _, r in high_variance.head(5).iterrows():
        direction = "over" if r["variance_dollar"] > 0 else "under"
        flags.append(
            f"{r['department']} — {r['line_item']} is "
            f"{abs(r['variance_pct']):.1f}% {direction} budget "
            f"(${abs(r['variance_dollar']):,.0f})."
        )
    return flags