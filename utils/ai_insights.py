"""
AI-powered insights engine with Google Gemini integration and rule-based fallback.
Provides data analysis, anomaly detection, trend analysis, and recommendations.
"""

import pandas as pd
import numpy as np


def generate_insights_gemini(df_summary, api_key):
    """
    Generate natural language insights using Google Gemini 2.5 Flash.

    Args:
        df_summary (str): A text summary of the dataset to analyze.
        api_key (str): Google Gemini API key.

    Returns:
        str or None: AI-generated insights about the data, or None on failure.
    """
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

        system_instruction = (
            "You are a senior data analyst preparing a briefing for stakeholders. "
            "Analyze the provided dataset summary and produce a structured report with these sections:\n\n"
            "## Executive Summary\nA 2-3 sentence overview of the dataset and its key characteristics.\n\n"
            "## Key Findings\nList 3-5 specific, quantitative findings. Cite exact numbers.\n\n"
            "## Patterns & Trends\nIdentify correlations, distributions, and temporal patterns.\n\n"
            "## Anomalies & Concerns\nFlag any data quality issues, outliers, or unexpected patterns.\n\n"
            "## Actionable Recommendations\nProvide 3-5 specific, actionable recommendations based on the data.\n\n"
            "Be precise, cite numbers, and use professional business language."
        )

        prompt = f"{system_instruction}\n\nPlease analyze this dataset summary and provide insights:\n\n{df_summary}"

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text

        return None

    except Exception:
        return None


def generate_insights_fallback(df):
    """
    Generate rule-based insights by analyzing the dataset without AI.

    Analyzes numeric and categorical columns to identify patterns,
    distributions, outliers, and key statistics.

    Args:
        df (pd.DataFrame): The dataset to analyze.

    Returns:
        dict: Dictionary with insight categories as keys and lists of insights as values.
    """
    insights = {
        "key_findings": [],
        "patterns": [],
        "concerns": [],
        "recommendations": []
    }

    if df.empty:
        insights["concerns"].append("The dataset is empty. No analysis can be performed.")
        return insights

    # Basic dataset info
    insights["key_findings"].append(
        f"Dataset contains {len(df)} records with {len(df.columns)} columns."
    )

    # Analyze numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        mean_val = df[col].mean()
        std_val = df[col].std()
        insights["key_findings"].append(
            f"{col}: Mean = {mean_val:.2f}, Std Dev = {std_val:.2f}"
        )

        # Check for high variability
        if std_val > mean_val * 0.5 and mean_val != 0:
            insights["patterns"].append(
                f"{col} shows high variability (CV = {std_val/mean_val:.2%})."
            )

    # Analyze categorical columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    for col in categorical_cols:
        n_unique = df[col].nunique()
        top_value = df[col].value_counts().index[0] if not df[col].value_counts().empty else "N/A"
        top_pct = (df[col].value_counts().iloc[0] / len(df) * 100) if not df[col].value_counts().empty else 0
        insights["key_findings"].append(
            f"{col}: {n_unique} unique values. Most common: '{top_value}' ({top_pct:.1f}%)"
        )

        # Check for imbalanced categories
        if top_pct > 50:
            insights["concerns"].append(
                f"{col} is dominated by '{top_value}' ({top_pct:.1f}%). "
                "Consider if this represents a data quality issue."
            )

    # Missing data analysis
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols) > 0:
        for col, count in missing_cols.items():
            pct = count / len(df) * 100
            insights["concerns"].append(
                f"{col} has {count} missing values ({pct:.1f}%)."
            )
        insights["recommendations"].append(
            "Address missing values through imputation or removal before detailed analysis."
        )
    else:
        insights["key_findings"].append("No missing values detected in the dataset.")

    # Correlation insights for numeric columns
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                r = corr.iloc[i, j]
                if abs(r) > 0.5:
                    strength = "strong" if abs(r) > 0.7 else "moderate"
                    direction = "positive" if r > 0 else "negative"
                    insights["patterns"].append(
                        f"{strength.capitalize()} {direction} correlation ({r:.2f}) "
                        f"between {numeric_cols[i]} and {numeric_cols[j]}."
                    )

    # Recommendations
    if len(numeric_cols) > 0:
        insights["recommendations"].append(
            "Consider segmenting the analysis by categorical variables for deeper insights."
        )
    if len(df) < 100:
        insights["recommendations"].append(
            "Dataset is relatively small. Results should be interpreted with caution."
        )
    if len(df) > 500:
        insights["recommendations"].append(
            "Dataset is large enough for meaningful statistical analysis and modeling."
        )

    return insights


def generate_summary_stats(df):
    """
    Generate comprehensive summary statistics for a dataset.

    Args:
        df (pd.DataFrame): The dataset to summarize.

    Returns:
        dict: Dictionary containing summary statistics for each column type.
    """
    stats = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "numeric_summary": {},
        "categorical_summary": {},
        "missing_values": {}
    }

    # Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        desc = df[numeric_cols].describe().round(2)
        stats["numeric_summary"] = desc.to_dict()

    # Categorical columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    for col in categorical_cols:
        stats["categorical_summary"][col] = {
            "unique_count": int(df[col].nunique()),
            "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A",
            "top_frequency": int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0
        }

    # Missing values
    missing = df.isnull().sum()
    stats["missing_values"] = {
        col: {"count": int(count), "percentage": round(count / len(df) * 100, 2)}
        for col, count in missing.items() if count > 0
    }

    return stats


def format_summary_as_markdown(df, stats):
    """
    Format summary statistics as clean markdown text suitable for LLM prompts.

    Args:
        df (pd.DataFrame): The dataset being summarized.
        stats (dict): Summary statistics dict from generate_summary_stats.

    Returns:
        str: Markdown-formatted summary text.
    """
    lines = []
    lines.append(f"## Dataset Overview")
    lines.append(f"- Rows: {stats['shape']['rows']}")
    lines.append(f"- Columns: {stats['shape']['columns']}")
    lines.append(f"- Column names: {', '.join(df.columns.tolist())}")
    lines.append("")

    # Numeric summary
    numeric_summary = stats.get("numeric_summary", {})
    if numeric_summary:
        lines.append("## Numeric Columns")
        lines.append("")
        # Build a markdown table
        cols = list(numeric_summary.keys())
        metrics = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
        header = "| Metric | " + " | ".join(cols) + " |"
        separator = "|---| " + " | ".join(["---"] * len(cols)) + " |"
        lines.append(header)
        lines.append(separator)
        for metric in metrics:
            row_values = []
            for col in cols:
                val = numeric_summary[col].get(metric, "N/A")
                row_values.append(str(val))
            lines.append(f"| {metric} | " + " | ".join(row_values) + " |")
        lines.append("")

    # Categorical summary
    cat_summary = stats.get("categorical_summary", {})
    if cat_summary:
        lines.append("## Categorical Columns")
        lines.append("")
        lines.append("| Column | Unique Values | Most Common | Frequency |")
        lines.append("|---|---|---|---|")
        for col, info in cat_summary.items():
            lines.append(
                f"| {col} | {info['unique_count']} | "
                f"{info['top_value']} | {info['top_frequency']} |"
            )
        lines.append("")

    # Missing values
    missing = stats.get("missing_values", {})
    if missing:
        lines.append("## Missing Values")
        lines.append("")
        lines.append("| Column | Count | Percentage |")
        lines.append("|---|---|---|")
        for col, info in missing.items():
            lines.append(f"| {col} | {info['count']} | {info['percentage']}% |")
    else:
        lines.append("## Missing Values")
        lines.append("No missing values detected.")

    return "\n".join(lines)


def detect_anomalies(df):
    """
    Detect anomalies in numeric columns using the IQR method.

    Args:
        df (pd.DataFrame): The dataset to analyze.

    Returns:
        dict: Dictionary with column names as keys and DataFrames of anomalous rows as values.
    """
    anomalies = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        outliers = df[mask]

        if len(outliers) > 0:
            anomalies[col] = {
                "count": len(outliers),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "outlier_rows": outliers.head(10)
            }

    return anomalies


def detect_trends(df, date_col=None, value_col=None):
    """
    Detect trends in data, supporting year-over-year or sequential changes.

    Args:
        df (pd.DataFrame): The dataset to analyze.
        date_col (str, optional): Column containing time/year information.
        value_col (str, optional): Column containing values to track.

    Returns:
        dict: Dictionary with trend information.
    """
    trends = {}

    if date_col and value_col and date_col in df.columns and value_col in df.columns:
        # Year-over-year analysis
        yearly = df.groupby(date_col)[value_col].mean().sort_index()

        if len(yearly) >= 2:
            changes = yearly.pct_change().dropna()
            trends["yearly_averages"] = yearly.round(2).to_dict()
            trends["year_over_year_change"] = changes.round(4).to_dict()
            trends["overall_trend"] = "increasing" if yearly.iloc[-1] > yearly.iloc[0] else "decreasing"
            trends["total_change_pct"] = round(
                (yearly.iloc[-1] - yearly.iloc[0]) / yearly.iloc[0] * 100, 2
            )
    else:
        # Auto-detect potential time columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        potential_time_cols = [c for c in df.columns if "year" in c.lower() or "date" in c.lower()]

        if potential_time_cols and numeric_cols:
            time_col = potential_time_cols[0]
            for num_col in numeric_cols[:3]:
                yearly = df.groupby(time_col)[num_col].mean().sort_index()
                if len(yearly) >= 2:
                    trends[f"{num_col}_by_{time_col}"] = {
                        "averages": yearly.round(2).to_dict(),
                        "trend": "increasing" if yearly.iloc[-1] > yearly.iloc[0] else "decreasing"
                    }

    return trends


def generate_recommendations(df):
    """
    Generate rule-based recommendations based on data patterns.

    Args:
        df (pd.DataFrame): The dataset to analyze.

    Returns:
        list: List of recommendation strings.
    """
    recommendations = []

    if df.empty:
        return ["Upload a dataset to receive recommendations."]

    # Check data completeness
    missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if missing_pct > 5:
        recommendations.append(
            f"Data completeness is {100-missing_pct:.1f}%. "
            "Consider data cleaning or imputation strategies."
        )
    elif missing_pct == 0:
        recommendations.append("Excellent data quality - no missing values detected.")

    # Check sample size
    if len(df) < 30:
        recommendations.append(
            "Small sample size. Statistical results may not be reliable. "
            "Consider collecting more data."
        )

    # Check for high cardinality categorical columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    for col in categorical_cols:
        n_unique = df[col].nunique()
        if n_unique > len(df) * 0.5:
            recommendations.append(
                f"'{col}' has very high cardinality ({n_unique} unique values). "
                "Consider grouping or encoding for analysis."
            )

    # Numeric column recommendations
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 2:
        recommendations.append(
            "Multiple numeric columns available. Consider correlation analysis "
            "and feature importance evaluation."
        )

    if len(numeric_cols) >= 3:
        recommendations.append(
            "Sufficient numeric features for clustering or dimensionality reduction."
        )

    # Check for potential grouping analysis
    if categorical_cols and numeric_cols:
        recommendations.append(
            f"Consider comparing {numeric_cols[0]} across different "
            f"{categorical_cols[0]} categories for segmentation insights."
        )

    return recommendations


def generate_data_quality_report(df):
    """
    Generate a comprehensive data quality report.

    Args:
        df (pd.DataFrame): The dataset to analyze.

    Returns:
        dict: Dictionary containing data quality metrics.
    """
    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "total_cells": len(df) * len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": {}
    }

    for col in df.columns:
        col_info = {
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "null_count": int(df[col].isnull().sum()),
            "null_percentage": round(df[col].isnull().sum() / len(df) * 100, 2),
            "unique_count": int(df[col].nunique()),
            "unique_percentage": round(df[col].nunique() / len(df) * 100, 2)
        }

        if df[col].dtype in ["int64", "float64"]:
            col_info["min"] = float(df[col].min()) if not df[col].isnull().all() else None
            col_info["max"] = float(df[col].max()) if not df[col].isnull().all() else None
            col_info["mean"] = round(float(df[col].mean()), 2) if not df[col].isnull().all() else None
        elif df[col].dtype == "object":
            col_info["sample_values"] = df[col].dropna().unique()[:5].tolist()

        report["columns"][col] = col_info

    # Overall quality score
    total_cells = report["total_cells"]
    filled_cells = sum(
        info["non_null_count"] for info in report["columns"].values()
    )
    report["completeness_score"] = round(filled_cells / total_cells * 100, 2) if total_cells > 0 else 0
    report["duplicate_percentage"] = round(
        report["duplicate_rows"] / report["total_rows"] * 100, 2
    ) if report["total_rows"] > 0 else 0

    return report
