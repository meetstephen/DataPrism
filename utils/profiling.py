"""Data profiling utilities - quality scoring, column profiles, correlation heatmaps, and AI commentary."""
import pandas as pd
import numpy as np


def compute_quality_score(df):
    """Compute a 0-100 data quality score based on completeness, duplicates, and type consistency.

    Returns an integer score.
    """
    if df is None or df.empty:
        return 0

    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols

    # Completeness (0-50 points)
    missing = int(df.isnull().sum().sum())
    completeness_ratio = (total_cells - missing) / total_cells if total_cells > 0 else 1
    completeness_score = completeness_ratio * 50

    # Duplicate penalty (0-25 points)
    dup_count = int(df.duplicated().sum())
    dup_ratio = dup_count / n_rows if n_rows > 0 else 0
    dup_score = max(0, 25 * (1 - dup_ratio * 5))  # penalize heavily

    # Type consistency (0-25 points) - mixed types in object columns
    type_score = 25.0
    object_cols = df.select_dtypes(include=["object"]).columns
    if len(object_cols) > 0:
        mixed_count = 0
        for col in object_cols:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                # Check if numeric-like values are mixed with text
                numeric_like = pd.to_numeric(non_null, errors="coerce").notna().sum()
                ratio = numeric_like / len(non_null)
                if 0.1 < ratio < 0.9:
                    mixed_count += 1
        if mixed_count > 0:
            type_score = max(0, 25 - (mixed_count / len(object_cols)) * 25)

    score = int(round(completeness_score + dup_score + type_score))
    return max(0, min(100, score))


def generate_column_profiles(df):
    """Generate per-column profile data.

    Returns a list of dicts with keys: column, dtype, non_null, null_pct,
    unique, mean, std, min, max, mode, sample_values.
    """
    if df is None or df.empty:
        return []

    profiles = []
    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        null_pct = round(null_count / n_rows * 100, 2) if n_rows > 0 else 0
        unique_count = int(series.nunique())

        profile = {
            "column": col,
            "dtype": str(series.dtype),
            "non_null": n_rows - null_count,
            "null_pct": null_pct,
            "unique": unique_count,
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "mode": None,
            "sample_values": [],
        }

        if pd.api.types.is_numeric_dtype(series):
            profile["mean"] = round(float(series.mean()), 4) if not series.dropna().empty else None
            profile["std"] = round(float(series.std()), 4) if not series.dropna().empty else None
            profile["min"] = float(series.min()) if not series.dropna().empty else None
            profile["max"] = float(series.max()) if not series.dropna().empty else None
        else:
            mode_vals = series.mode()
            if not mode_vals.empty:
                profile["mode"] = str(mode_vals.iloc[0])

        # Sample non-null values
        non_null_vals = series.dropna().head(5).tolist()
        profile["sample_values"] = [str(v) for v in non_null_vals]

        profiles.append(profile)

    return profiles


def generate_correlation_heatmap_data(df):
    """Generate correlation matrix data for numeric columns.

    Returns a dict with keys: columns (list), matrix (2D list of floats).
    Returns None if fewer than 2 numeric columns.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return None

    corr = df[numeric_cols].corr().round(4)
    return {
        "columns": corr.columns.tolist(),
        "matrix": corr.values.tolist(),
    }


def ai_profiler_commentary(df, api_key=None):
    """Generate AI commentary on data quality using Gemini.

    Returns a string with the AI commentary, or a fallback message on failure.
    """
    if df is None or df.empty:
        return "No data available for profiling commentary."

    try:
        from utils.ai_client import generate_content, get_api_key

        key = api_key or get_api_key()
        if not key:
            return _rule_based_commentary(df)

        n_rows, n_cols = df.shape
        missing = int(df.isnull().sum().sum())
        total_cells = n_rows * n_cols
        completeness = ((total_cells - missing) / total_cells * 100) if total_cells > 0 else 100
        duplicates = int(df.duplicated().sum())
        quality_score = compute_quality_score(df)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        stats_preview = ""
        if numeric_cols:
            stats_preview = df[numeric_cols[:5]].describe().to_string()

        prompt = (
            "You are a senior data quality analyst. Provide a brief (3-5 sentences) "
            "commentary on this dataset's quality and readiness for analysis.\n\n"
            f"Shape: {n_rows} rows x {n_cols} columns\n"
            f"Quality Score: {quality_score}/100\n"
            f"Completeness: {completeness:.1f}%\n"
            f"Duplicates: {duplicates}\n"
            f"Column types: {dict(df.dtypes.value_counts())}\n"
            f"Stats preview:\n{stats_preview}\n"
        )

        text, err = generate_content(prompt, api_key=key)
        if text:
            return text
        return _rule_based_commentary(df)
    except Exception:
        return _rule_based_commentary(df)


def _rule_based_commentary(df):
    """Fallback rule-based profiling commentary."""
    n_rows, n_cols = df.shape
    missing = int(df.isnull().sum().sum())
    total_cells = n_rows * n_cols
    completeness = ((total_cells - missing) / total_cells * 100) if total_cells > 0 else 100
    duplicates = int(df.duplicated().sum())
    score = compute_quality_score(df)

    parts = []
    parts.append(f"Dataset has {n_rows:,} rows and {n_cols} columns with a quality score of {score}/100.")

    if completeness >= 99:
        parts.append("Data completeness is excellent with virtually no missing values.")
    elif completeness >= 90:
        parts.append(f"Data completeness is good at {completeness:.1f}%, though some cleaning may help.")
    else:
        parts.append(f"Data completeness is {completeness:.1f}% - significant cleaning is recommended before analysis.")

    if duplicates > 0:
        parts.append(f"Found {duplicates:,} duplicate rows that may need attention.")

    if score >= 80:
        parts.append("Overall, this dataset is well-suited for analysis.")
    elif score >= 50:
        parts.append("The dataset needs some preparation but is workable.")
    else:
        parts.append("Substantial data quality issues detected - thorough cleaning is strongly recommended.")

    return " ".join(parts)
