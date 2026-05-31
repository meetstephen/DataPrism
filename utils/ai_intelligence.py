"""AI-powered intelligence helpers for generating insights and explanations."""
import json


def generate_insight_cards(analysis_context, api_key):
    """Call Gemini to generate structured insight cards.
    Returns dict with keys: findings, risks, opportunities, recommendations.
    Each value is a list of strings.
    Returns (cards_dict, error).
    """
    try:
        from utils.ai_client import generate_content

        prompt = f"""Based on this analysis context, generate structured insights.
Return ONLY valid JSON with these exact keys:
- "findings": list of 3-5 key findings (strings)
- "risks": list of 2-3 potential risks or data quality concerns (strings)
- "opportunities": list of 2-3 opportunities for further analysis (strings)
- "recommendations": list of 3-5 actionable recommendations (strings)

Analysis context:
{analysis_context}

Return ONLY the JSON object, no markdown formatting or code blocks."""

        system = "You are a data analyst. Return only valid JSON. No markdown code fences."
        text, err = generate_content(prompt, api_key=api_key, system_instruction=system)

        if err:
            return {"findings": [], "risks": [], "opportunities": [], "recommendations": []}, err

        # Parse JSON response
        try:
            # Strip possible markdown code fences
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            cards = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            # Fallback: try to extract JSON from the response
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                cards = json.loads(text[start:end])
            except (ValueError, json.JSONDecodeError):
                cards = {"findings": [text], "risks": [], "opportunities": [], "recommendations": []}

        # Ensure all keys exist
        for key in ["findings", "risks", "opportunities", "recommendations"]:
            if key not in cards:
                cards[key] = []

        return cards, None
    except Exception as e:
        return {"findings": [], "risks": [], "opportunities": [], "recommendations": []}, f"Insight generation failed: {str(e)}"


def explain_this_number(value, column_name, df, api_key):
    """Use Gemini to explain what a specific value means in context.
    Returns (text, error).
    """
    try:
        from utils.ai_client import generate_content
        import pandas as pd
        import numpy as np

        # Gather context about the column
        series = df[column_name]
        stats = {}
        if pd.api.types.is_numeric_dtype(series):
            stats = {
                "mean": round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "std": round(float(series.std()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
                "percentile_25": round(float(series.quantile(0.25)), 2),
                "percentile_75": round(float(series.quantile(0.75)), 2),
            }
        else:
            top_vals = series.value_counts().head(5)
            stats = {
                "top_values": {str(k): int(v) for k, v in top_vals.items()},
                "unique_count": int(series.nunique()),
                "total_rows": len(series),
            }

        prompt = f"""Explain what the value "{value}" means for the column "{column_name}" in this dataset.

Column statistics: {json.dumps(stats)}
Dataset has {len(df)} rows and {len(df.columns)} columns.

Explain:
1. What this value represents in context
2. How it compares to the distribution (is it typical, unusual, extreme?)
3. What might drive or influence this value

Keep your response to 3-4 sentences, clear and actionable."""

        system = "You are a data analyst explaining findings to a non-technical stakeholder."
        text, err = generate_content(prompt, api_key=api_key, system_instruction=system)
        return text, err
    except Exception as e:
        return None, f"Explanation failed: {str(e)}"


def generate_executive_summary_brief(df, api_key):
    """Generate a 400-word formal executive brief.
    Structure: Situation, Key Metrics, Findings, Risks, Recommendations.
    Returns (text, error).
    """
    try:
        from utils.ai_client import generate_content
        import pandas as pd
        import numpy as np

        # Build dataset context
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        metrics_summary = []
        for col in numeric_cols[:8]:
            metrics_summary.append(
                f"- {col}: mean={df[col].mean():.2f}, median={df[col].median():.2f}, "
                f"std={df[col].std():.2f}"
            )

        cat_summary = []
        for col in cat_cols[:5]:
            top = df[col].value_counts().head(3)
            cat_summary.append(f"- {col}: {', '.join([f'{k}({v})' for k, v in top.items()])}")

        null_info = df.isnull().sum()
        null_cols = null_info[null_info > 0]
        null_text = ", ".join([f"{c}({v})" for c, v in null_cols.head(5).items()]) if len(null_cols) > 0 else "None"

        prompt = f"""Write a formal 400-word executive summary brief for this dataset analysis.

Dataset: {len(df)} rows, {len(df.columns)} columns
Numeric columns ({len(numeric_cols)}):
{chr(10).join(metrics_summary)}

Categorical columns ({len(cat_cols)}):
{chr(10).join(cat_summary)}

Missing data: {null_text}
Duplicate rows: {df.duplicated().sum()}

Structure your brief with these sections:
1. **Situation** - What this data represents and its scope
2. **Key Metrics** - The most important numbers
3. **Findings** - Notable patterns and insights
4. **Risks** - Data quality or business risks identified
5. **Recommendations** - Actionable next steps

Write professionally and concisely. Target exactly 400 words."""

        system = "You are a senior data analyst writing an executive brief. Be formal, precise, and actionable."
        text, err = generate_content(prompt, api_key=api_key, system_instruction=system)
        return text, err
    except Exception as e:
        return None, f"Executive summary generation failed: {str(e)}"
