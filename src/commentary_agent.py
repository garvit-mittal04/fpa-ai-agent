"""
commentary_agent.py
-------------------
Generates board-ready management commentary and risk flags using the Groq API.

Upgrades:
- Stronger fallback commentary (not just an error message)
- Better handling of clean/stable datasets
- Adds recommendations and leadership focus
- More robust text cleaning
- Keeps risk flags available even when API is down
"""

import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> Groq:
    """Initialize Groq client at call time so env vars are always fresh."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file or Streamlit secrets."
        )
    return Groq(api_key=api_key)


def _clean_commentary(text: str) -> str:
    """
    Post-process LLM output to fix common formatting issues.
    - Replaces accidental backtick-number patterns with $
    - Normalizes extra whitespace
    """
    if not text:
        return ""

    text = re.sub(r"`\s*(-?\$?\d)", r"$\1", text)
    text = re.sub(r"\$\$", "$", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _format_currency(value) -> str:
    return f"${value:,.0f}"


def _safe_pct(value) -> str:
    try:
        return f"{float(value):+.1f}%"
    except Exception:
        return "N/A"


def _top_variances_text(df, direction: str, n: int = 3) -> str:
    """
    direction:
        unfavorable -> most negative variance_dollar
        favorable   -> most positive variance_dollar
    """
    if df.empty:
        return "None"

    if direction == "unfavorable":
        subset = df[df["variance_dollar"] < 0].nsmallest(n, "variance_dollar")
    else:
        subset = df[df["variance_dollar"] > 0].nlargest(n, "variance_dollar")

    if subset.empty:
        return "None"

    return "\n".join([
        f"- {r['department']} | {r['line_item']} | "
        f"{_format_currency(r['variance_dollar'])} ({_safe_pct(r['variance_pct'])})"
        for _, r in subset.iterrows()
    ])


def _department_summary_text(dept_summary_df) -> str:
    if dept_summary_df is None or dept_summary_df.empty:
        return "None"

    lines = []
    for _, r in dept_summary_df.iterrows():
        # Works with your current dataframe structure:
        # department, total_actual, total_budget, variance_dollar, variance_pct
        dept = r.iloc[0]
        actual = r.iloc[1]
        budget = r.iloc[2]
        var_pct = r.iloc[4]
        lines.append(
            f"- {dept}: Actual {_format_currency(actual)} vs Budget {_format_currency(budget)} "
            f"({_safe_pct(var_pct)})"
        )
    return "\n".join(lines)


def _recommendations_text(variance_df, anomaly_summary: dict, dept_summary_df) -> str:
    """
    Build simple rule-based recommendations to give the model stronger guidance
    and provide fallback commentary when API is unavailable.
    """
    recommendations = []

    total_var = variance_df["variance_dollar"].sum() if not variance_df.empty else 0
    total_var_pct = (
        (variance_df["actual_amount"].sum() - variance_df["budget_amount"].sum())
        / variance_df["budget_amount"].sum() * 100
        if not variance_df.empty and variance_df["budget_amount"].sum() != 0
        else 0
    )

    if total_var < 0:
        recommendations.append(
            "Leadership should review the largest under-budget line items to confirm whether the shortfall reflects lower activity, delayed spend, or execution timing."
        )
    elif total_var > 0:
        recommendations.append(
            "Leadership should validate whether the overspend is strategic and temporary or whether tighter cost controls are required next month."
        )
    else:
        recommendations.append(
            "Overall performance is broadly in line with budget, so focus should shift to monitoring department-level pockets of deviation."
        )

    if anomaly_summary.get("total_anomalies", 0) > 0:
        recommendations.append(
            "Flagged anomalies should be reviewed with department owners to distinguish one-time items from emerging run-rate issues."
        )
    else:
        recommendations.append(
            "No statistically significant anomalies were detected, suggesting current performance is operating within a normal range."
        )

    if dept_summary_df is not None and not dept_summary_df.empty:
        worst = dept_summary_df.iloc[0]
        recommendations.append(
            f"Near-term follow-up should prioritize {worst.iloc[0]}, which shows one of the largest department-level gaps versus plan."
        )

    return " ".join(recommendations)


def _rule_based_commentary(variance_df, anomaly_summary: dict, dept_summary_df) -> str:
    """
    Strong fallback commentary for when the LLM is unavailable.
    Always returns usable management commentary.
    """
    if variance_df is None or variance_df.empty:
        return (
            "No financial data was available for commentary generation. "
            "Please upload actuals and budget files, then rerun the analysis."
        )

    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    top_unfavorable = variance_df[variance_df["variance_dollar"] < 0].nsmallest(3, "variance_dollar")
    top_favorable = variance_df[variance_df["variance_dollar"] > 0].nlargest(3, "variance_dollar")

    anomaly_count = anomaly_summary.get("total_anomalies", 0)
    anomaly_depts = anomaly_summary.get("departments_affected", [])

    para1 = (
        f"Overall performance closed at {_format_currency(total_actual)} versus a budget of "
        f"{_format_currency(total_budget)}, resulting in a net variance of "
        f"{_format_currency(total_var)} ({total_var_pct:+.1f}%). "
        f"This indicates that the organization is {'above' if total_var > 0 else 'below' if total_var < 0 else 'in line with'} "
        f"plan for the period."
    )

    if not top_unfavorable.empty:
        unfav_text = "; ".join([
            f"{r['department']} {r['line_item']} ({_format_currency(r['variance_dollar'])}, {_safe_pct(r['variance_pct'])})"
            for _, r in top_unfavorable.iterrows()
        ])
    else:
        unfav_text = "no material unfavorable variances were identified"

    if not top_favorable.empty:
        fav_text = "; ".join([
            f"{r['department']} {r['line_item']} ({_format_currency(r['variance_dollar'])}, {_safe_pct(r['variance_pct'])})"
            for _, r in top_favorable.iterrows()
        ])
    else:
        fav_text = "no material favorable variances were identified"

    para2 = (
        f"The largest unfavorable drivers were {unfav_text}. "
        f"Offsetting these, the strongest favorable contributions came from {fav_text}."
    )

    if anomaly_count > 0:
        para3 = (
            f"The anomaly review flagged {anomaly_count} line items across "
            f"{', '.join(anomaly_depts) if anomaly_depts else 'multiple departments'}. "
            f"These items should be reviewed with budget owners to determine whether they reflect timing, mix shifts, or emerging operational issues."
        )
    else:
        para3 = (
            "The anomaly review did not identify any statistically unusual line items, "
            "which suggests current performance is broadly stable relative to the uploaded dataset."
        )

    para4 = _recommendations_text(variance_df, anomaly_summary, dept_summary_df)

    return "\n\n".join([para1, para2, para3, para4])


def generate_commentary(variance_df, anomaly_summary: dict, dept_summary_df) -> str:
    """
    Generate 3-4 paragraph board-ready management commentary.

    Returns a strong rule-based fallback if the API is unavailable or fails.
    """
    if variance_df is None or variance_df.empty:
        return (
            "No variance data is available to generate commentary. "
            "Please upload valid actuals and budget files and rerun the analysis."
        )

    total_actual = variance_df["actual_amount"].sum()
    total_budget = variance_df["budget_amount"].sum()
    total_var = total_actual - total_budget
    total_var_pct = (total_var / total_budget * 100) if total_budget != 0 else 0

    anomaly_count = anomaly_summary.get("total_anomalies", 0)
    anomaly_depts = anomaly_summary.get("departments_affected", [])

    unfav_text = _top_variances_text(variance_df, "unfavorable", n=3)
    fav_text = _top_variances_text(variance_df, "favorable", n=3)
    dept_text = _department_summary_text(dept_summary_df)
    recommendations = _recommendations_text(variance_df, anomaly_summary, dept_summary_df)

    prompt = f"""
You are a senior FP&A analyst writing a board-ready monthly management commentary.

Overall Performance
- Total Actual: {_format_currency(total_actual)}
- Total Budget: {_format_currency(total_budget)}
- Net Variance: {_format_currency(total_var)} ({total_var_pct:+.1f}%)

Department Summary
{dept_text}

Top 3 Unfavorable Variances
{unfav_text}

Top 3 Favorable Variances
{fav_text}

Anomaly Review
- Total anomalies flagged: {anomaly_count}
- Departments affected: {", ".join(anomaly_depts) if anomaly_depts else "None"}

Recommended leadership focus
{recommendations}

Write a concise 3-4 paragraph commentary that:
1. Summarizes overall performance vs budget
2. Explains the key drivers by department and line item
3. States whether leadership attention is required and why
4. Ends with forward-looking next-step guidance for the next month

Tone:
- professional
- direct
- executive
- not robotic
- not overly dramatic

Rules:
- Do not use bullet points
- Always use the $ symbol for money
- Be specific and business-oriented
- If anomalies are zero, explicitly say performance appears stable and no statistically significant anomalies were detected
"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
        )
        commentary = response.choices[0].message.content
        cleaned = _clean_commentary(commentary)
        return cleaned if cleaned else _rule_based_commentary(variance_df, anomaly_summary, dept_summary_df)

    except Exception:
        return _rule_based_commentary(variance_df, anomaly_summary, dept_summary_df)


def generate_risk_flags(variance_df) -> list:
    """
    Generate 3-5 concise risk flag strings for items >10% off budget.

    Falls back to rule-based logic if the API is unavailable.
    """
    if variance_df is None or variance_df.empty:
        return ["No data available for risk evaluation."]

    high_variance = variance_df[abs(variance_df["variance_pct"]) > 10].copy()
    high_variance = high_variance.reindex(
        high_variance["variance_pct"].abs().sort_values(ascending=False).index
    ).head(10)

    if high_variance.empty:
        return ["No significant risk flags detected — all line items within 10% of budget."]

    items_text = "\n".join([
        f"- {r['department']} | {r['line_item']} | "
        f"{_format_currency(r['variance_dollar'])} ({_safe_pct(r['variance_pct'])})"
        for _, r in high_variance.iterrows()
    ])

    prompt = f"""
You are a senior FP&A analyst. Based on these high-variance line items (>10% off budget),
generate 3-5 concise leadership risk flags.

High Variance Items:
{items_text}

Rules:
- Each flag must be one sentence
- Start each sentence with the department name
- Use the $ symbol for money
- Focus on business risk, not just restating the numbers
"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        raw = response.choices[0].message.content
        flags = [ln.strip("- •").strip() for ln in raw.strip().split("\n") if ln.strip()]
        return flags if flags else _rule_based_flags(high_variance)

    except Exception:
        return _rule_based_flags(high_variance)


def _rule_based_flags(high_variance) -> list:
    """Rule-based fallback — no API required."""
    flags = []

    for _, r in high_variance.head(5).iterrows():
        if r["variance_dollar"] > 0:
            direction = "over budget"
            business_risk = "which may require tighter cost control or validation of one-time spend"
        else:
            direction = "under budget"
            business_risk = "which may indicate delayed execution, lower activity, or timing differences"

        flags.append(
            f"{r['department']} — {r['line_item']} is {abs(r['variance_pct']):.1f}% {direction} "
            f"({_format_currency(abs(r['variance_dollar']))}), {business_risk}."
        )

    return flags
