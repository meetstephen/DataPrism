"""AI intelligence features: insight cards, number explanations, executive summaries."""
import pandas as pd
import numpy as np


def generate_insight_cards(df, api_key=None):
    """Generate auto-insight cards from the dataset.

    Returns a list of dicts with keys: type (finding/risk/opportunity/recommendation),
    title, content.
    """
    if df is None or df.empty:
        return []

    cards = []
    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Missing data insight
    missing_total = int(df.isnull().sum().sum())
    total_cells = n_rows * n_cols
    completeness = ((total_cells - missing_total) / total_cells * 100) if total_cells > 0 else 100
    if completeness < 90:
        cards.append({
            "type": "risk",
            "title": "Data Completeness Concern",
            "content": f"Dataset is only {completeness:.1f}% complete with {missing_total:,} missing values. Consider cleaning before analysis.",
        })
    elif completeness >= 99:
        cards.append({
            "type": "finding",
            "title": "Excellent Data Quality",
            "content": f"Dataset is {completeness:.1f}% complete - ready for reliable analysis.",
        })

    # Outlier detection
    for col in numeric_cols[:5]:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            outliers = ((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum()
            if outliers > n_rows * 0.05:
                cards.append({
                    "type": "risk",
                    "title": f"Outliers in {col}",
                    "content": f"Found {outliers} outliers ({outliers/n_rows*100:.1f}%) in '{col}'. This may skew statistical analyses.",
                })

    # High correlation
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().abs()
        corr_vals = corr.values.copy()
        np.fill_diagonal(corr_vals, 0)
        max_corr = corr_vals.max()
        if max_corr > 0.85:
            max_idx = np.unravel_index(corr_vals.argmax(), corr_vals.shape)
            col_a = corr.columns[max_idx[0]]
            col_b = corr.columns[max_idx[1]]
            cards.append({
                "type": "finding",
                "title": "Strong Correlation Detected",
                "content": f"'{col_a}' and '{col_b}' have a correlation of {max_corr:.2f}. Consider if one is redundant.",
            })

    # Categorical dominance
    for col in cat_cols[:3]:
        top_freq = df[col].value_counts(normalize=True).iloc[0] if not df[col].value_counts().empty else 0
        if top_freq > 0.7:
            top_val = df[col].value_counts().index[0]
            cards.append({
                "type": "opportunity",
                "title": f"Dominant Category in {col}",
                "content": f"'{top_val}' accounts for {top_freq*100:.1f}% of values. Consider segmenting for deeper analysis.",
            })

    # Size recommendation
    if n_rows > 10000:
        cards.append({
            "type": "recommendation",
            "title": "Large Dataset",
            "content": f"With {n_rows:,} rows, consider sampling for exploratory analysis then validating on the full set.",
        })

    # AI-enhanced cards
    if api_key:
        ai_cards = _ai_generate_cards(df, api_key)
        if ai_cards:
            cards.extend(ai_cards)

    return cards


def _ai_generate_cards(df, api_key):
    """Use AI to generate additional insight cards."""
    try:
        from utils.ai_client import generate_content

        n_rows, n_cols = df.shape
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        stats_text = df[numeric_cols[:5]].describe().to_string() if numeric_cols else "No numeric columns"

        prompt = (
            "Analyze this dataset summary and provide exactly 2 insights as JSON array. "
            "Each item should have: type (one of: finding, risk, opportunity, recommendation), "
            "title (short), content (1-2 sentences with specific numbers).\n\n"
            f"Shape: {n_rows} rows x {n_cols} columns\n"
            f"Columns: {list(df.columns[:15])}\n"
            f"Stats:\n{stats_text}\n\n"
            "Return ONLY valid JSON array, no markdown."
        )

        text, err = generate_content(prompt, api_key=api_key)
        if text:
            import json
            # Try to parse JSON from the response
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            cards = json.loads(text)
            if isinstance(cards, list):
                return cards[:3]
    except Exception:
        pass
    return []


def explain_this_number(df, column, value, api_key=None):
    """Explain a specific value in context of the column distribution.

    Returns a string explanation.
    """
    if df is None or column not in df.columns:
        return "Cannot explain: column not found."

    series = df[column].dropna()
    if len(series) == 0:
        return "Cannot explain: column has no data."

    # Build context
    if pd.api.types.is_numeric_dtype(series):
        mean_val = series.mean()
        std_val = series.std()
        median_val = series.median()
        percentile = (series < value).sum() / len(series) * 100

        context = (
            f"Value {value} in column '{column}':\n"
            f"- Percentile: {percentile:.1f}th\n"
            f"- Mean: {mean_val:.2f}, Median: {median_val:.2f}, Std: {std_val:.2f}\n"
            f"- Distance from mean: {abs(value - mean_val)/std_val:.2f} standard deviations\n"
        )

        if api_key:
            try:
                from utils.ai_client import generate_content
                prompt = (
                    "Explain this number to a business user in 2-3 simple sentences. "
                    "Use plain language, mention the percentile and what it means practically.\n\n"
                    f"{context}"
                )
                text, err = generate_content(prompt, api_key=api_key)
                if text:
                    return text
            except Exception:
                pass

        # Rule-based explanation
        if percentile >= 95:
            return f"This value ({value}) is in the top 5% for '{column}' (95th percentile). It is {abs(value - mean_val)/std_val:.1f} standard deviations above the mean of {mean_val:.2f}."
        elif percentile <= 5:
            return f"This value ({value}) is in the bottom 5% for '{column}' (5th percentile). It is {abs(value - mean_val)/std_val:.1f} standard deviations below the mean of {mean_val:.2f}."
        else:
            return f"This value ({value}) is at the {percentile:.0f}th percentile for '{column}'. The mean is {mean_val:.2f} and median is {median_val:.2f}."
    else:
        freq = (series == value).sum()
        total = len(series)
        pct = freq / total * 100
        return f"'{value}' appears {freq} times in '{column}' ({pct:.1f}% of all values)."


def generate_executive_summary_brief(df, goal="General analysis", api_key=None):
    """Generate a concise executive summary (3-5 bullet points).

    Returns a string with the summary.
    """
    if df is None or df.empty:
        return "No data available for executive summary."

    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    missing = int(df.isnull().sum().sum())
    completeness = ((n_rows * n_cols - missing) / (n_rows * n_cols) * 100) if n_rows * n_cols > 0 else 100

    if api_key:
        try:
            from utils.ai_client import generate_content
            stats_text = df[numeric_cols[:5]].describe().to_string() if numeric_cols else ""
            prompt = (
                "Write a concise executive summary (3-5 bullet points) for business stakeholders. "
                f"Analysis goal: {goal}\n\n"
                f"Dataset: {n_rows:,} rows x {n_cols} columns\n"
                f"Completeness: {completeness:.1f}%\n"
                f"Columns: {list(df.columns[:15])}\n"
                f"Stats:\n{stats_text}\n"
                f"Sample:\n{df.head(3).to_string()}\n\n"
                "Use bullet points with specific numbers. Be actionable."
            )
            text, err = generate_content(prompt, api_key=api_key)
            if text:
                return text
        except Exception:
            pass

    # Rule-based summary
    bullets = []
    bullets.append(f"Dataset contains {n_rows:,} records across {n_cols} variables ({len(numeric_cols)} numeric, {len(cat_cols)} categorical).")
    bullets.append(f"Data completeness is {completeness:.1f}% with {missing:,} missing values total.")

    if numeric_cols:
        top_col = numeric_cols[0]
        mean_val = df[top_col].mean()
        bullets.append(f"Key metric '{top_col}' averages {mean_val:,.2f} across the dataset.")

    if cat_cols:
        top_cat = cat_cols[0]
        n_unique = df[top_cat].nunique()
        bullets.append(f"Primary category '{top_cat}' has {n_unique} distinct values.")

    bullets.append("Recommended next steps: clean missing data, explore correlations, and segment by key categories.")

    return "\n".join(f"- {b}" for b in bullets)
