"""Dashboard builder utilities - KPI detection, chart registry, auto-build."""
import pandas as pd
import numpy as np


# Chart registry: 11 chart types available for dashboards
CHART_REGISTRY = {
    "bar": {"label": "Bar Chart", "icon": "📊", "min_cols": 2, "needs_numeric": True},
    "line": {"label": "Line Chart", "icon": "📈", "min_cols": 2, "needs_numeric": True},
    "scatter": {"label": "Scatter Plot", "icon": "🔵", "min_cols": 2, "needs_numeric": True},
    "histogram": {"label": "Histogram", "icon": "📉", "min_cols": 1, "needs_numeric": True},
    "box": {"label": "Box Plot", "icon": "📦", "min_cols": 2, "needs_numeric": True},
    "pie": {"label": "Pie Chart", "icon": "🥧", "min_cols": 2, "needs_numeric": False},
    "heatmap": {"label": "Correlation Heatmap", "icon": "🔥", "min_cols": 2, "needs_numeric": True},
    "area": {"label": "Area Chart", "icon": "🏔️", "min_cols": 2, "needs_numeric": True},
    "violin": {"label": "Violin Plot", "icon": "🎻", "min_cols": 2, "needs_numeric": True},
    "treemap": {"label": "Treemap", "icon": "🌳", "min_cols": 2, "needs_numeric": False},
    "funnel": {"label": "Funnel Chart", "icon": "🔻", "min_cols": 2, "needs_numeric": True},
}


def detect_kpi_columns(df):
    """Detect columns suitable for KPI display.

    Returns a list of dicts with keys: column, value, label, change (optional).
    KPIs are numeric columns with meaningful aggregates.
    """
    if df is None or df.empty:
        return []

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    kpis = []

    for col in numeric_cols[:6]:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        mean_val = series.mean()
        # Detect if this looks like a count, percentage, or measure
        if series.max() <= 1 and series.min() >= 0:
            # Likely a ratio/percentage
            kpis.append({
                "column": col,
                "value": round(float(mean_val * 100), 1),
                "label": f"Avg {col} (%)",
                "format": "percent",
            })
        elif series.dtype in [np.int64, np.int32] and series.min() >= 0:
            # Likely a count
            kpis.append({
                "column": col,
                "value": int(series.sum()),
                "label": f"Total {col}",
                "format": "integer",
            })
        else:
            kpis.append({
                "column": col,
                "value": round(float(mean_val), 2),
                "label": f"Avg {col}",
                "format": "decimal",
            })

    return kpis[:4]  # Max 4 KPI cards


def build_kpi_card_data(df, column, agg="mean"):
    """Build data for a single KPI card.

    Returns a dict with: value, label, delta (change from first half to second half).
    """
    if df is None or column not in df.columns:
        return None

    series = df[column].dropna()
    if len(series) == 0:
        return None

    if agg == "sum":
        value = float(series.sum())
    elif agg == "count":
        value = int(len(series))
    elif agg == "max":
        value = float(series.max())
    elif agg == "min":
        value = float(series.min())
    else:
        value = float(series.mean())

    # Compute delta (compare first half vs second half)
    mid = len(series) // 2
    delta = None
    if mid > 0:
        first_half = series.iloc[:mid].mean()
        second_half = series.iloc[mid:].mean()
        if first_half != 0:
            delta = round((second_half - first_half) / abs(first_half) * 100, 1)

    return {
        "value": round(value, 2),
        "label": f"{agg.capitalize()} of {column}",
        "delta": delta,
    }


def auto_build_dashboard(df):
    """Automatically build a dashboard configuration based on the dataset.

    Returns a dict with: kpis (list), charts (list of chart configs).
    """
    if df is None or df.empty:
        return {"kpis": [], "charts": []}

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Auto KPIs
    kpis = detect_kpi_columns(df)

    # Auto charts
    charts = []

    # Chart 1: Distribution of first numeric column
    if numeric_cols:
        charts.append({
            "type": "histogram",
            "config": {"x": numeric_cols[0]},
            "title": f"Distribution of {numeric_cols[0]}",
        })

    # Chart 2: Bar chart of first categorical column
    if cat_cols:
        low_card = [c for c in cat_cols if df[c].nunique() <= 15]
        if low_card:
            charts.append({
                "type": "bar",
                "config": {"x": low_card[0], "y": "count"},
                "title": f"Count by {low_card[0]}",
            })

    # Chart 3: Correlation heatmap
    if len(numeric_cols) >= 2:
        charts.append({
            "type": "heatmap",
            "config": {"columns": numeric_cols[:8]},
            "title": "Correlation Heatmap",
        })

    # Chart 4: Scatter of top correlated pair
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().abs()
        corr_vals = corr.values.copy()
        np.fill_diagonal(corr_vals, 0)
        max_idx = np.unravel_index(corr_vals.argmax(), corr_vals.shape)
        col_a = corr.columns[max_idx[0]]
        col_b = corr.columns[max_idx[1]]
        charts.append({
            "type": "scatter",
            "config": {"x": col_a, "y": col_b},
            "title": f"{col_a} vs {col_b}",
        })

    # Chart 5: Line chart if there is a time-like column
    date_cols = [c for c in df.columns if any(kw in c.lower() for kw in ["year", "date", "month", "time", "period"])]
    if date_cols and numeric_cols:
        charts.append({
            "type": "line",
            "config": {"x": date_cols[0], "y": numeric_cols[0]},
            "title": f"{numeric_cols[0]} over {date_cols[0]}",
        })

    # Chart 6: Box plot if categorical + numeric exist
    if cat_cols and numeric_cols:
        low_card_cats = [c for c in cat_cols if df[c].nunique() <= 10]
        if low_card_cats:
            charts.append({
                "type": "box",
                "config": {"x": low_card_cats[0], "y": numeric_cols[0]},
                "title": f"{numeric_cols[0]} by {low_card_cats[0]}",
            })

    return {"kpis": kpis, "charts": charts[:6]}
