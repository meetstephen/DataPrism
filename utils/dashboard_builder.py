"""Dashboard building utilities: KPI detection, chart registry, and auto-dashboard."""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def detect_kpi_columns(df):
    """Heuristically pick top numeric columns suitable for KPI cards.
    Excludes ID-like columns and those with very low variance.
    Returns list of column names (max 6).
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    candidates = []

    for col in numeric_cols:
        col_lower = col.lower()
        # Skip ID-like columns
        if any(x in col_lower for x in ['id', 'index', 'key', 'pk', 'fk']):
            continue
        series = df[col].dropna()
        if len(series) < 2:
            continue
        # Skip binary columns (only 0/1)
        unique_vals = series.nunique()
        if unique_vals <= 2:
            continue
        # Prefer columns with reasonable range and variance
        cv = series.std() / series.mean() if series.mean() != 0 else 0
        candidates.append((col, abs(cv)))

    # Sort by coefficient of variation (descending) - more interesting KPIs
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in candidates[:6]]


def build_kpi_card_data(df, col, date_col=None):
    """Compute KPI card data for a column.
    Returns dict with value, delta, sparkline_data.
    """
    series = df[col].dropna()
    if series.empty:
        return {"value": 0, "delta": None, "sparkline_data": []}

    current_value = round(float(series.iloc[-1]) if len(series) > 0 else 0, 2)
    mean_value = round(float(series.mean()), 2)

    delta = None
    sparkline_data = []

    if date_col and date_col in df.columns:
        work_df = df[[date_col, col]].dropna().copy()
        work_df[date_col] = pd.to_datetime(work_df[date_col], errors='coerce')
        work_df = work_df.dropna().sort_values(date_col)

        if len(work_df) >= 2:
            mid = len(work_df) // 2
            prev_mean = work_df[col].iloc[:mid].mean()
            curr_mean = work_df[col].iloc[mid:].mean()
            if prev_mean != 0:
                delta = round(float((curr_mean - prev_mean) / prev_mean * 100), 1)
            sparkline_data = work_df[col].tail(20).tolist()
    else:
        # Without date, use overall stats
        if len(series) >= 2:
            mid = len(series) // 2
            prev_mean = series.iloc[:mid].mean()
            curr_mean = series.iloc[mid:].mean()
            if prev_mean != 0:
                delta = round(float((curr_mean - prev_mean) / prev_mean * 100), 1)
            sparkline_data = series.tail(20).tolist()

    return {
        "value": mean_value,
        "delta": delta,
        "sparkline_data": sparkline_data,
    }


def _build_bar(df, x, y, color=None, title="Bar Chart"):
    return px.bar(df, x=x, y=y, color=color, title=title)


def _build_line(df, x, y, color=None, title="Line Chart"):
    return px.line(df, x=x, y=y, color=color, title=title)


def _build_area(df, x, y, color=None, title="Area Chart"):
    return px.area(df, x=x, y=y, color=color, title=title)


def _build_scatter(df, x, y, color=None, title="Scatter Plot"):
    return px.scatter(df, x=x, y=y, color=color, title=title)


def _build_pie(df, x, y, color=None, title="Pie Chart"):
    return px.pie(df, names=x, values=y, title=title)


def _build_donut(df, x, y, color=None, title="Donut Chart"):
    fig = px.pie(df, names=x, values=y, title=title, hole=0.4)
    return fig


def _build_box(df, x, y, color=None, title="Box Plot"):
    return px.box(df, x=x, y=y, color=color, title=title)


def _build_histogram(df, x, y=None, color=None, title="Histogram"):
    return px.histogram(df, x=x, color=color, title=title)


def _build_waterfall(df, x, y, color=None, title="Waterfall Chart"):
    values = df[y].tolist() if y in df.columns else []
    labels = df[x].tolist() if x in df.columns else []
    fig = go.Figure(go.Waterfall(
        x=labels[:20],
        y=values[:20],
        name=title,
    ))
    fig.update_layout(title=title)
    return fig


def _build_gauge(df, x, y, color=None, title="Gauge"):
    value = float(df[y].mean()) if y in df.columns else 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={"axis": {"range": [df[y].min(), df[y].max()]}} if y in df.columns else {},
    ))
    return fig


def _build_treemap(df, x, y, color=None, title="Treemap"):
    return px.treemap(df, path=[x], values=y, title=title)


CHART_REGISTRY = {
    "bar": _build_bar,
    "line": _build_line,
    "area": _build_area,
    "scatter": _build_scatter,
    "pie": _build_pie,
    "donut": _build_donut,
    "box": _build_box,
    "histogram": _build_histogram,
    "waterfall": _build_waterfall,
    "gauge": _build_gauge,
    "treemap": _build_treemap,
}


def auto_build_dashboard(df, api_key=None):
    """Analyze the schema and return a list of chart specs.
    If api_key is provided, uses Gemini to pick charts; otherwise uses rule-based heuristic.
    Returns list of dicts: [{chart_type, x, y, color, title}].
    """
    import json as json_mod

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

    # Also detect date-like object columns
    for col in cat_cols[:]:
        try:
            parsed = pd.to_datetime(df[col], errors='coerce')
            if parsed.notna().sum() / len(df) > 0.7:
                date_cols.append(col)
                cat_cols.remove(col)
        except Exception:
            pass

    charts = []

    # Try AI-powered chart selection
    if api_key:
        try:
            from utils.ai_client import generate_content

            col_info = f"Numeric: {numeric_cols[:10]}, Categorical: {cat_cols[:10]}, Date: {date_cols[:5]}"
            prompt = f"""Given a dataset with these columns:
{col_info}

Suggest 4-6 charts that would best visualize this data.
Return ONLY valid JSON array of objects with keys: chart_type, x, y, color (optional), title.
Available chart_types: bar, line, area, scatter, pie, donut, box, histogram, waterfall, gauge, treemap.

Return ONLY the JSON array, no explanation."""

            system = "You are a data visualization expert. Return only valid JSON."
            text, err = generate_content(prompt, api_key=api_key, system_instruction=system)

            if text and not err:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    cleaned = cleaned.strip()
                try:
                    ai_charts = json_mod.loads(cleaned)
                    if isinstance(ai_charts, list) and len(ai_charts) > 0:
                        return ai_charts[:6]
                except (json_mod.JSONDecodeError, ValueError):
                    pass
        except Exception:
            pass

    # Rule-based fallback
    # 1. If date column exists, add a line chart
    if date_cols and numeric_cols:
        charts.append({
            "chart_type": "line",
            "x": date_cols[0],
            "y": numeric_cols[0],
            "color": None,
            "title": f"{numeric_cols[0]} Over Time",
        })

    # 2. Histogram of first numeric column
    if numeric_cols:
        charts.append({
            "chart_type": "histogram",
            "x": numeric_cols[0],
            "y": None,
            "color": None,
            "title": f"Distribution of {numeric_cols[0]}",
        })

    # 3. Bar chart if categorical + numeric
    if cat_cols and numeric_cols:
        charts.append({
            "chart_type": "bar",
            "x": cat_cols[0],
            "y": numeric_cols[0],
            "color": None,
            "title": f"{numeric_cols[0]} by {cat_cols[0]}",
        })

    # 4. Scatter plot if 2+ numeric columns
    if len(numeric_cols) >= 2:
        charts.append({
            "chart_type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1],
            "color": cat_cols[0] if cat_cols else None,
            "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
        })

    # 5. Box plot if categorical + numeric
    if cat_cols and numeric_cols:
        y_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
        charts.append({
            "chart_type": "box",
            "x": cat_cols[0],
            "y": y_col,
            "color": None,
            "title": f"{y_col} by {cat_cols[0]}",
        })

    # 6. Pie chart for categorical distribution
    if cat_cols:
        vc = df[cat_cols[0]].value_counts()
        if len(vc) <= 10:
            charts.append({
                "chart_type": "pie",
                "x": cat_cols[0],
                "y": cat_cols[0],
                "color": None,
                "title": f"Distribution of {cat_cols[0]}",
            })

    return charts[:6]
