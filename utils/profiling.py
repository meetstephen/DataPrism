"""Data profiling utilities for quality scoring and column analysis."""
import pandas as pd
import numpy as np


def compute_quality_score(df):
    """Compute a 0-100 data quality score based on null rate, duplicate rate,
    type consistency, and outlier rate.
    """
    if df is None or df.empty:
        return 0

    total_cells = df.shape[0] * df.shape[1]

    # Null rate (0-1)
    null_rate = df.isna().sum().sum() / total_cells if total_cells > 0 else 0

    # Duplicate rate (0-1)
    duplicate_rate = df.duplicated().sum() / len(df) if len(df) > 0 else 0

    # Type consistency: fraction of columns where inferred type matches actual
    type_issues = 0
    for col in df.columns:
        if df[col].dtype == object:
            # Check if numeric values are stored as strings
            try:
                numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
                non_null_count = df[col].notna().sum()
                if non_null_count > 0 and numeric_count / non_null_count > 0.8:
                    type_issues += 1
            except Exception:
                pass
    type_issue_rate = type_issues / len(df.columns) if len(df.columns) > 0 else 0

    # Outlier rate for numeric columns (IQR method)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    outlier_count = 0
    total_numeric_values = 0
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count += ((series < lower) | (series > upper)).sum()
        total_numeric_values += len(series)
    outlier_rate = outlier_count / total_numeric_values if total_numeric_values > 0 else 0

    # Weighted score (higher is better)
    score = 100 * (
        1.0
        - 0.35 * null_rate
        - 0.25 * duplicate_rate
        - 0.20 * type_issue_rate
        - 0.20 * outlier_rate
    )
    return max(0, min(100, round(score, 1)))


def generate_column_profiles(df):
    """Generate detailed profiles for each column.
    Returns a list of dicts with dtype, null_pct, unique_count, top_values,
    and mini distribution data.
    """
    if df is None or df.empty:
        return []

    profiles = []
    for col in df.columns:
        series = df[col]
        null_pct = round(series.isna().sum() / len(series) * 100, 2) if len(series) > 0 else 0
        unique_count = int(series.nunique())

        # Top values (top 5 by frequency)
        top_vals = series.value_counts().head(5)
        top_values = [{"value": str(k), "count": int(v)} for k, v in top_vals.items()]

        # Mini distribution
        distribution = {}
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                try:
                    counts, bin_edges = np.histogram(clean, bins=min(20, len(clean)))
                    distribution = {
                        "type": "histogram",
                        "bin_edges": [round(float(x), 4) for x in bin_edges],
                        "counts": [int(x) for x in counts],
                    }
                except Exception:
                    distribution = {"type": "histogram", "bin_edges": [], "counts": []}
        else:
            vc = series.value_counts().head(10)
            distribution = {
                "type": "categorical",
                "labels": [str(k) for k in vc.index],
                "counts": [int(v) for v in vc.values],
            }

        profiles.append({
            "column": col,
            "dtype": str(series.dtype),
            "null_pct": null_pct,
            "unique_count": unique_count,
            "top_values": top_values,
            "distribution": distribution,
        })

    return profiles


def generate_correlation_heatmap_data(df):
    """Compute correlation matrix for numeric columns.
    Returns dict with 'matrix' (DataFrame) and 'high_correlation_pairs' list
    of pairs with |r| > 0.85.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty or numeric_df.shape[1] < 2:
        return {"matrix": pd.DataFrame(), "high_correlation_pairs": []}

    corr_matrix = numeric_df.corr()

    # Find high correlation pairs
    high_pairs = []
    cols = corr_matrix.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr_matrix.iloc[i, j]
            if abs(r) > 0.85:
                high_pairs.append({
                    "col_a": cols[i],
                    "col_b": cols[j],
                    "correlation": round(float(r), 4),
                    "flagged": True,
                })

    return {"matrix": corr_matrix, "high_correlation_pairs": high_pairs}


def ai_profiler_commentary(df, api_key):
    """Use Gemini to generate a quality assessment and cleaning recommendations.
    Returns (text, error).
    """
    try:
        from utils.ai_client import generate_content

        score = compute_quality_score(df)
        profiles = generate_column_profiles(df)

        # Build a concise summary for the prompt
        col_summary = []
        for p in profiles[:15]:  # Limit to 15 columns for prompt size
            col_summary.append(
                f"- {p['column']} ({p['dtype']}): {p['null_pct']}% null, "
                f"{p['unique_count']} unique values"
            )
        col_text = "\n".join(col_summary)

        prompt = f"""Analyze this dataset quality profile and provide:
1. A 2-3 sentence assessment of overall data quality.
2. Top 3 specific cleaning recommendations.

Dataset: {len(df)} rows, {len(df.columns)} columns
Quality Score: {score}/100

Column profiles:
{col_text}

Keep your response concise and actionable."""

        system = "You are a data quality expert. Be concise and specific."
        text, err = generate_content(prompt, api_key=api_key, system_instruction=system)
        return text, err
    except Exception as e:
        return None, f"Profiling commentary failed: {str(e)}"
