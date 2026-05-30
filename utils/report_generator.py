"""
Report generator for creating comprehensive HTML analysis reports.
Generates standalone HTML files with embedded charts, statistics, and optional AI summaries.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def get_report_css():
    """Return CSS stylesheet string for the HTML report. Uses a professional dark theme
    that matches the app (background #1E1E2E, text #FFFFFF, accent #4CAF50, cards with #2D2D44)."""
    return """
    body {
        background-color: #1E1E2E;
        color: #FFFFFF;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 20px 40px;
        line-height: 1.6;
    }
    h1 {
        color: #4CAF50;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 10px;
        margin-top: 30px;
    }
    h2 {
        color: #81C784;
        margin-top: 30px;
        border-bottom: 1px solid #3D3D5C;
        padding-bottom: 8px;
    }
    h3 {
        color: #A5D6A7;
        margin-top: 20px;
    }
    h4 {
        color: #C8E6C9;
        margin-top: 15px;
    }
    .report-header {
        text-align: center;
        padding: 30px;
        background-color: #2D2D44;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .report-header h1 {
        border-bottom: none;
        margin: 0;
        font-size: 2.2em;
    }
    .report-header p {
        color: #B0B0B0;
        margin: 5px 0;
    }
    .card {
        background-color: #2D2D44;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        background-color: #2D2D44;
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background-color: #3D3D5C;
        color: #4CAF50;
        padding: 12px 15px;
        text-align: left;
        font-weight: 600;
    }
    td {
        padding: 10px 15px;
        border-bottom: 1px solid #3D3D5C;
        color: #E0E0E0;
    }
    tr:hover td {
        background-color: #3D3D5C;
    }
    .chart-container {
        background-color: #2D2D44;
        border-radius: 8px;
        padding: 15px;
        margin: 20px 0;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    .metric-card {
        background-color: #2D2D44;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        border-left: 4px solid #4CAF50;
    }
    .metric-card .value {
        font-size: 1.8em;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-card .label {
        color: #B0B0B0;
        font-size: 0.9em;
        margin-top: 5px;
    }
    .quality-bar {
        background-color: #3D3D5C;
        border-radius: 4px;
        height: 20px;
        overflow: hidden;
        margin: 5px 0;
    }
    .quality-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s;
    }
    .footer {
        text-align: center;
        padding: 20px;
        margin-top: 40px;
        border-top: 1px solid #3D3D5C;
        color: #808080;
        font-size: 0.85em;
    }
    .summary-text {
        background-color: #2D2D44;
        border-radius: 8px;
        padding: 20px 25px;
        margin: 15px 0;
        border-left: 4px solid #4CAF50;
        line-height: 1.8;
    }
    """


def create_chart_html(fig):
    """Convert a Plotly figure to an embeddable HTML div string."""
    if fig is None:
        return ""
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def create_stats_table_html(df):
    """Generate an HTML table of summary statistics for numeric and categorical columns."""
    if df is None or df.empty:
        return "<p>No data available for statistics.</p>"

    html_parts = []

    # Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        html_parts.append("<h3>Numeric Columns</h3>")
        desc = df[numeric_cols].describe().T.round(2)
        html_parts.append("<table>")
        html_parts.append("<tr><th>Column</th>")
        for stat in desc.columns:
            html_parts.append(f"<th>{stat}</th>")
        html_parts.append("</tr>")
        for col_name in desc.index:
            html_parts.append(f"<tr><td><strong>{col_name}</strong></td>")
            for stat in desc.columns:
                html_parts.append(f"<td>{desc.loc[col_name, stat]}</td>")
            html_parts.append("</tr>")
        html_parts.append("</table>")

    # Categorical columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if categorical_cols:
        html_parts.append("<h3>Categorical Columns</h3>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Column</th><th>Unique Values</th><th>Mode</th><th>Mode Frequency</th></tr>")
        for col in categorical_cols:
            n_unique = df[col].nunique()
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "N/A"
            mode_freq = int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0
            html_parts.append(
                f"<tr><td><strong>{col}</strong></td>"
                f"<td>{n_unique}</td>"
                f"<td>{mode_val}</td>"
                f"<td>{mode_freq}</td></tr>"
            )
        html_parts.append("</table>")

    if not html_parts:
        return "<p>No numeric or categorical columns found.</p>"

    return "\n".join(html_parts)


def generate_executive_summary(df, api_key=None):
    """
    Generate a 3-5 paragraph executive summary.
    If api_key provided, use Gemini. Otherwise, generate rule-based summary.
    Returns string (plain text).
    """
    if df is None or df.empty:
        return "No data available for generating an executive summary."

    if api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

            # Build data summary for context
            shape_info = f"{len(df)} rows and {len(df.columns)} columns"
            col_info = ", ".join(df.columns.tolist()[:20])
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            stats_info = ""
            if numeric_cols:
                stats_info = df[numeric_cols].describe().to_string()

            prompt = (
                "Write a concise 3-5 paragraph executive summary of this dataset "
                "for a business audience. Focus on key findings, notable patterns, "
                "and actionable recommendations.\n\n"
                f"Dataset: {shape_info}\n"
                f"Columns: {col_info}\n\n"
                f"Statistics:\n{stats_info}\n\n"
                f"First few rows:\n{df.head(5).to_string()}"
            )

            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception:
            pass

    # Rule-based fallback
    return _generate_rule_based_summary(df)


def _generate_rule_based_summary(df):
    """Generate a rule-based executive summary from dataset statistics."""
    paragraphs = []

    # Paragraph 1: Overview
    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    paragraphs.append(
        f"This dataset contains {n_rows:,} records across {n_cols} variables. "
        f"Of these, {len(numeric_cols)} are numeric and {len(categorical_cols)} are categorical. "
        f"The data columns include: {', '.join(df.columns.tolist()[:10])}"
        f"{'...' if len(df.columns) > 10 else ''}."
    )

    # Paragraph 2: Key numeric findings
    if numeric_cols:
        top_col = numeric_cols[0]
        mean_val = df[top_col].mean()
        std_val = df[top_col].std()
        min_val = df[top_col].min()
        max_val = df[top_col].max()
        paragraphs.append(
            f"Analyzing key numeric variables, '{top_col}' has a mean of {mean_val:.2f} "
            f"with a standard deviation of {std_val:.2f}, ranging from {min_val:.2f} to {max_val:.2f}. "
            f"{'High variability suggests significant differences across records. ' if std_val > mean_val * 0.5 and mean_val != 0 else ''}"
            f"The dataset contains {len(numeric_cols)} quantitative measures suitable for statistical analysis."
        )

    # Paragraph 3: Categorical findings
    if categorical_cols:
        top_cat = categorical_cols[0]
        n_unique = df[top_cat].nunique()
        mode_val = df[top_cat].mode().iloc[0] if not df[top_cat].mode().empty else "N/A"
        paragraphs.append(
            f"Among categorical variables, '{top_cat}' contains {n_unique} distinct values "
            f"with '{mode_val}' being the most frequent. "
            f"This distribution may indicate natural groupings suitable for segmented analysis."
        )

    # Paragraph 4: Data quality
    missing_total = df.isnull().sum().sum()
    total_cells = n_rows * n_cols
    completeness = ((total_cells - missing_total) / total_cells * 100) if total_cells > 0 else 100
    duplicates = df.duplicated().sum()
    paragraphs.append(
        f"Data quality assessment shows {completeness:.1f}% completeness with "
        f"{missing_total:,} missing values across the dataset. "
        f"There are {duplicates:,} duplicate rows detected. "
        f"{'The data is well-suited for analysis.' if completeness > 95 else 'Data cleaning may be recommended before detailed analysis.'}"
    )

    return "\n\n".join(paragraphs)


def generate_html_report(df, title="Data Analysis Report", include_ai_summary=False, api_key=None):
    """
    Generate a complete standalone HTML report.

    Args:
        df: DataFrame to analyze
        title: Report title
        include_ai_summary: Whether to include AI-generated executive summary
        api_key: Gemini API key (required if include_ai_summary=True)

    Returns:
        str: Complete HTML document string
    """
    if df is None or df.empty:
        return _generate_empty_report(title)

    css = get_report_css()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_parts = []

    # DOCTYPE and head
    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html lang='en'>")
    html_parts.append("<head>")
    html_parts.append("<meta charset='UTF-8'>")
    html_parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html_parts.append(f"<title>{title}</title>")
    html_parts.append("<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>")
    html_parts.append(f"<style>{css}</style>")
    html_parts.append("</head>")
    html_parts.append("<body>")

    # Report header
    html_parts.append("<div class='report-header'>")
    html_parts.append(f"<h1>{title}</h1>")
    html_parts.append(f"<p>Generated on {now}</p>")
    html_parts.append(f"<p>{len(df):,} rows x {len(df.columns)} columns</p>")
    html_parts.append("</div>")

    # Executive Summary
    html_parts.append("<h2>Executive Summary</h2>")
    summary = generate_executive_summary(df, api_key=api_key if include_ai_summary else None)
    html_parts.append(f"<div class='summary-text'>{_text_to_html(summary)}</div>")

    # Dataset Overview
    html_parts.append("<h2>Dataset Overview</h2>")
    html_parts.append(_generate_overview_section(df))

    # Summary Statistics
    html_parts.append("<h2>Summary Statistics</h2>")
    html_parts.append("<div class='card'>")
    html_parts.append(create_stats_table_html(df))
    html_parts.append("</div>")

    # Distribution Charts
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        html_parts.append("<h2>Distribution Analysis</h2>")
        for col in numeric_cols[:8]:  # Limit to 8 charts
            try:
                fig = px.histogram(
                    df, x=col, title=f"Distribution of {col}",
                    template="plotly_dark",
                    color_discrete_sequence=["#4CAF50"]
                )
                fig.update_layout(
                    paper_bgcolor="#2D2D44",
                    plot_bgcolor="#1E1E2E",
                    font_color="#FFFFFF",
                    height=350
                )
                html_parts.append("<div class='chart-container'>")
                html_parts.append(create_chart_html(fig))
                html_parts.append("</div>")
            except Exception:
                continue

    # Correlation Matrix
    if len(numeric_cols) >= 2:
        html_parts.append("<h2>Correlation Analysis</h2>")
        try:
            corr_matrix = df[numeric_cols].corr()
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns.tolist(),
                y=corr_matrix.index.tolist(),
                colorscale="RdYlGn",
                zmin=-1, zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate="%{text}",
                hovertemplate="(%{x}, %{y}): %{z:.2f}<extra></extra>"
            ))
            fig.update_layout(
                title="Correlation Matrix",
                template="plotly_dark",
                paper_bgcolor="#2D2D44",
                plot_bgcolor="#1E1E2E",
                font_color="#FFFFFF",
                height=500
            )
            html_parts.append("<div class='chart-container'>")
            html_parts.append(create_chart_html(fig))
            html_parts.append("</div>")
        except Exception:
            html_parts.append("<p>Could not generate correlation matrix.</p>")

    # Data Quality Section
    html_parts.append("<h2>Data Quality</h2>")
    html_parts.append(_generate_quality_section(df))

    # Footer
    html_parts.append(f"<div class='footer'>")
    html_parts.append(f"<p>Report generated on {now} | Community College Data Analyzer</p>")
    html_parts.append("</div>")

    html_parts.append("</body>")
    html_parts.append("</html>")

    return "\n".join(html_parts)


def _generate_empty_report(title):
    """Generate a minimal report for empty dataframes."""
    css = get_report_css()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class='report-header'>
<h1>{title}</h1>
<p>Generated on {now}</p>
</div>
<div class='card'>
<p>No data available. The provided dataset is empty.</p>
</div>
<div class='footer'>
<p>Report generated on {now} | Community College Data Analyzer</p>
</div>
</body>
</html>"""


def _generate_overview_section(df):
    """Generate the dataset overview section HTML."""
    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    memory_usage = df.memory_usage(deep=True).sum()

    if memory_usage > 1_000_000:
        memory_str = f"{memory_usage / 1_000_000:.1f} MB"
    else:
        memory_str = f"{memory_usage / 1_000:.1f} KB"

    html = f"""
    <div class='metric-grid'>
        <div class='metric-card'>
            <div class='value'>{n_rows:,}</div>
            <div class='label'>Rows</div>
        </div>
        <div class='metric-card'>
            <div class='value'>{n_cols}</div>
            <div class='label'>Columns</div>
        </div>
        <div class='metric-card'>
            <div class='value'>{len(numeric_cols)}</div>
            <div class='label'>Numeric Columns</div>
        </div>
        <div class='metric-card'>
            <div class='value'>{len(categorical_cols)}</div>
            <div class='label'>Categorical Columns</div>
        </div>
        <div class='metric-card'>
            <div class='value'>{memory_str}</div>
            <div class='label'>Memory Usage</div>
        </div>
    </div>
    <div class='card'>
        <h3>Column Details</h3>
        <table>
            <tr><th>Column</th><th>Type</th><th>Non-Null Count</th><th>Null %</th></tr>
    """
    for col in df.columns:
        null_pct = df[col].isnull().sum() / len(df) * 100
        non_null = df[col].notna().sum()
        html += f"<tr><td>{col}</td><td>{df[col].dtype}</td><td>{non_null:,}</td><td>{null_pct:.1f}%</td></tr>"

    html += "</table></div>"
    return html


def _generate_quality_section(df):
    """Generate the data quality section HTML."""
    n_rows = len(df)
    total_cells = n_rows * len(df.columns)
    missing_total = df.isnull().sum().sum()
    completeness = ((total_cells - missing_total) / total_cells * 100) if total_cells > 0 else 100
    duplicates = df.duplicated().sum()
    dup_pct = (duplicates / n_rows * 100) if n_rows > 0 else 0

    # Color based on completeness
    if completeness >= 95:
        bar_color = "#4CAF50"
    elif completeness >= 80:
        bar_color = "#FFC107"
    else:
        bar_color = "#F44336"

    html = f"""
    <div class='card'>
        <h3>Completeness: {completeness:.1f}%</h3>
        <div class='quality-bar'>
            <div class='quality-fill' style='width: {completeness}%; background-color: {bar_color};'></div>
        </div>
        <div class='metric-grid'>
            <div class='metric-card'>
                <div class='value'>{missing_total:,}</div>
                <div class='label'>Missing Values</div>
            </div>
            <div class='metric-card'>
                <div class='value'>{duplicates:,}</div>
                <div class='label'>Duplicate Rows ({dup_pct:.1f}%)</div>
            </div>
            <div class='metric-card'>
                <div class='value'>{total_cells:,}</div>
                <div class='label'>Total Cells</div>
            </div>
        </div>
    """

    # Missing values per column
    missing_cols = df.isnull().sum()
    missing_cols = missing_cols[missing_cols > 0]
    if len(missing_cols) > 0:
        html += "<h3>Missing Values by Column</h3>"
        html += "<table><tr><th>Column</th><th>Missing</th><th>Percentage</th></tr>"
        for col, count in missing_cols.items():
            pct = count / n_rows * 100
            html += f"<tr><td>{col}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>"
        html += "</table>"
    else:
        html += "<p>No missing values detected. Data is fully complete.</p>"

    html += "</div>"
    return html


def _text_to_html(text):
    """Convert plain text with newlines to HTML paragraphs."""
    if not text:
        return "<p>No summary available.</p>"
    paragraphs = text.strip().split("\n\n")
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p:
            html_paragraphs.append(f"<p>{p}</p>")
    return "\n".join(html_paragraphs) if html_paragraphs else f"<p>{text}</p>"
