"""
Dashboard - Interactive KPI cards, chart library, and auto-build dashboard.
"""

import streamlit as st
st.set_page_config(page_title="Dashboard", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_empty_state
inject_global_css()
from utils.data_loader import ensure_builtin_data
ensure_builtin_data()

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_generator import generate_dataset
from utils.ai_client import get_api_key
from utils.dashboard_builder import (
    detect_kpi_columns,
    build_kpi_card_data,
    auto_build_dashboard,
    CHART_REGISTRY,
)

st.title("\U0001F4CA Dashboard")
st.markdown("Interactive dashboard with KPI cards, chart library, and auto-build capabilities.")

# Initialize session state for dashboard
if "dashboard_charts" not in st.session_state:
    st.session_state.dashboard_charts = []
if "dashboard_filters" not in st.session_state:
    st.session_state.dashboard_filters = {}

# Data source selection
if "df" not in st.session_state:
    st.session_state.df = generate_dataset()

data_source_options = ["Built-in Community College Data", "Uploaded Data"]
if "online_df" in st.session_state and st.session_state.online_df is not None:
    data_source_options.append("Online Data")
if st.session_state.get("working_df") is not None:
    data_source_options.append("Cleaned Data")

data_source = st.radio(
    "Select Data Source:",
    data_source_options,
    horizontal=True,
    key="dash_data_source"
)

df = None
if data_source == "Built-in Community College Data":
    df = st.session_state.df.copy()
elif data_source == "Online Data":
    if "online_df" in st.session_state and st.session_state.online_df is not None:
        df = st.session_state.online_df.copy()
elif data_source == "Cleaned Data":
    if st.session_state.get("working_df") is not None:
        df = st.session_state.working_df.copy()
else:
    if st.session_state.get("uploaded_df") is not None:
        df = st.session_state.uploaded_df.copy()

if df is None or df.empty:
    render_empty_state("\U0001F4CA", "No Data for Dashboard", "Upload or load a dataset to build your dashboard.")
    st.page_link("pages/2_Upload_and_Analyze.py", label="Go to Upload & Analyze", icon="\U0001F4E4")
    st.stop()

# Column type detection
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
all_columns = df.columns.tolist()

# Detect date columns
date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
for col in categorical_cols[:]:
    try:
        parsed = pd.to_datetime(df[col], errors='coerce')
        if parsed.notna().sum() / max(len(df), 1) > 0.7:
            date_cols.append(col)
    except Exception:
        pass

# --- Sidebar Global Filters ---
with st.sidebar:
    st.header("Dashboard Filters")

    # Date range filter
    if date_cols:
        filter_date_col = st.selectbox("Date Column for Filter", date_cols, key="dash_filter_date_col")
        try:
            date_series = pd.to_datetime(df[filter_date_col], errors='coerce').dropna()
            if not date_series.empty:
                min_date = date_series.min().date()
                max_date = date_series.max().date()
                date_start = st.date_input("Start Date", value=min_date, min_value=min_date,
                                           max_value=max_date, key="dash_date_start")
                date_end = st.date_input("End Date", value=max_date, min_value=min_date,
                                         max_value=max_date, key="dash_date_end")
                st.session_state.dashboard_filters["date_col"] = filter_date_col
                st.session_state.dashboard_filters["date_start"] = date_start
                st.session_state.dashboard_filters["date_end"] = date_end
        except Exception:
            pass

    # Categorical filter
    if categorical_cols:
        filter_cat_col = st.selectbox("Category Filter Column", categorical_cols, key="dash_filter_cat_col")
        cat_options = df[filter_cat_col].dropna().unique().tolist()
        selected_cats = st.multiselect("Filter Values", cat_options,
                                        default=cat_options, key="dash_filter_cats")
        st.session_state.dashboard_filters["cat_col"] = filter_cat_col
        st.session_state.dashboard_filters["cat_values"] = selected_cats

    st.markdown("---")
    if st.button("Clear All Filters", key="dash_clear_filters"):
        st.session_state.dashboard_filters = {}
        st.rerun()


def apply_dashboard_filters(dataframe):
    """Apply global dashboard filters to a dataframe."""
    filtered = dataframe.copy()
    filters = st.session_state.get("dashboard_filters", {})

    # Apply date filter
    if "date_col" in filters and "date_start" in filters and "date_end" in filters:
        try:
            date_col = filters["date_col"]
            if date_col in filtered.columns:
                date_series = pd.to_datetime(filtered[date_col], errors='coerce')
                start = pd.Timestamp(filters["date_start"])
                end = pd.Timestamp(filters["date_end"])
                mask = (date_series >= start) & (date_series <= end)
                filtered = filtered[mask | date_series.isna()]
        except Exception:
            pass

    # Apply categorical filter
    if "cat_col" in filters and "cat_values" in filters:
        try:
            cat_col = filters["cat_col"]
            cat_vals = filters["cat_values"]
            if cat_col in filtered.columns and cat_vals:
                filtered = filtered[filtered[cat_col].isin(cat_vals)]
        except Exception:
            pass

    return filtered


# Apply filters to working dataframe
filtered_df = apply_dashboard_filters(df)
st.info(f"Dashboard data: {len(filtered_df)} rows (filtered from {len(df)} total)")

st.markdown("---")

# --- KPI Cards Row ---
st.markdown("### Key Performance Indicators")
kpi_columns = detect_kpi_columns(filtered_df)

if kpi_columns:
    # Detect date column for delta/sparkline
    kpi_date_col = date_cols[0] if date_cols else None
    kpi_cols_layout = st.columns(min(len(kpi_columns), 5))

    for i, kpi_col in enumerate(kpi_columns[:5]):
        kpi_data = build_kpi_card_data(filtered_df, kpi_col, date_col=kpi_date_col)
        with kpi_cols_layout[i]:
            delta_str = f"{kpi_data['delta']}%" if kpi_data["delta"] is not None else None
            st.metric(kpi_col, f"{kpi_data['value']:,.2f}", delta=delta_str)

            # Mini sparkline
            if kpi_data["sparkline_data"] and len(kpi_data["sparkline_data"]) > 2:
                fig_spark = go.Figure()
                fig_spark.add_trace(go.Scatter(
                    y=kpi_data["sparkline_data"],
                    mode="lines",
                    line=dict(color="#00D4FF", width=1.5),
                    showlegend=False,
                ))
                fig_spark.update_layout(
                    height=60, margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_spark, use_container_width=True, key=f"spark_{kpi_col}")
else:
    st.info("No suitable KPI columns detected in this dataset.")

st.markdown("---")

# --- Chart Library Section ---
st.markdown("### Chart Library")
st.caption("Build custom charts and add them to your dashboard.")

chart_types_display = {
    "Bar": "bar", "Line": "line", "Area": "area", "Scatter": "scatter",
    "Pie": "pie", "Donut": "donut", "Box Plot": "box",
    "Histogram": "histogram", "Waterfall": "waterfall", "Gauge": "gauge",
    "Treemap": "treemap",
}

lib_col1, lib_col2, lib_col3, lib_col4 = st.columns(4)
with lib_col1:
    chart_type_label = st.selectbox("Chart Type", list(chart_types_display.keys()), key="dash_chart_type")
with lib_col2:
    chart_x = st.selectbox("X Column", all_columns, key="dash_chart_x")
with lib_col3:
    chart_y = st.selectbox("Y Column", numeric_cols if numeric_cols else all_columns, key="dash_chart_y")
with lib_col4:
    color_options = ["None"] + categorical_cols
    chart_color = st.selectbox("Color Column", color_options, key="dash_chart_color")

if st.button("Add to Dashboard", key="dash_add_chart", type="primary"):
    chart_spec = {
        "chart_type": chart_types_display[chart_type_label],
        "x": chart_x,
        "y": chart_y,
        "color": chart_color if chart_color != "None" else None,
        "title": f"{chart_type_label}: {chart_y} by {chart_x}",
    }
    st.session_state.dashboard_charts.append(chart_spec)
    st.success(f"Added {chart_type_label} chart to dashboard!")

st.markdown("---")

# --- Auto-Build Dashboard ---
st.markdown("### Auto-Build Dashboard")
st.caption("Let AI or heuristics automatically select the best charts for your data.")

api_key = get_api_key()
if st.button("Auto-Build Dashboard", key="dash_auto_build", type="primary"):
    with st.spinner("Analyzing data and building dashboard..."):
        try:
            auto_charts = auto_build_dashboard(filtered_df, api_key=api_key)
            if auto_charts:
                st.markdown("**Auto-Generated Charts:**")
                auto_cols = st.columns(2)
                for idx, spec in enumerate(auto_charts):
                    chart_type = spec.get("chart_type", "bar")
                    x = spec.get("x")
                    y = spec.get("y")
                    color = spec.get("color")
                    title = spec.get("title", f"Chart {idx + 1}")

                    if chart_type in CHART_REGISTRY and x and x in filtered_df.columns:
                        try:
                            build_fn = CHART_REGISTRY[chart_type]
                            if y and y in filtered_df.columns:
                                fig = build_fn(filtered_df, x, y, color=color, title=title)
                            else:
                                fig = build_fn(filtered_df, x, x, color=color, title=title)
                            with auto_cols[idx % 2]:
                                st.plotly_chart(fig, use_container_width=True, key=f"auto_{idx}")
                        except Exception as chart_err:
                            with auto_cols[idx % 2]:
                                st.warning(f"Could not render: {title} ({str(chart_err)[:60]})")
            else:
                st.info("No charts could be auto-generated for this dataset.")
        except Exception as e:
            st.error(f"Auto-build failed: {str(e)}")

st.markdown("---")

# --- Dashboard Display Area ---
st.markdown("### Your Dashboard")

if st.session_state.dashboard_charts:
    dash_cols = st.columns(2)
    charts_to_remove = []

    for idx, spec in enumerate(st.session_state.dashboard_charts):
        chart_type = spec.get("chart_type", "bar")
        x = spec.get("x")
        y = spec.get("y")
        color = spec.get("color")
        title = spec.get("title", f"Chart {idx + 1}")

        with dash_cols[idx % 2]:
            if chart_type in CHART_REGISTRY and x and x in filtered_df.columns:
                try:
                    build_fn = CHART_REGISTRY[chart_type]
                    if y and y in filtered_df.columns:
                        fig = build_fn(filtered_df, x, y, color=color, title=title)
                    else:
                        fig = build_fn(filtered_df, x, x, color=color, title=title)
                    st.plotly_chart(fig, use_container_width=True, key=f"dash_chart_{idx}")
                except Exception as chart_err:
                    st.warning(f"Error rendering chart: {str(chart_err)[:80]}")
            else:
                st.warning(f"Cannot render chart: column '{x}' not found or chart type '{chart_type}' invalid.")

            if st.button("Remove", key=f"dash_remove_{idx}"):
                charts_to_remove.append(idx)

    # Remove marked charts
    if charts_to_remove:
        for idx in sorted(charts_to_remove, reverse=True):
            st.session_state.dashboard_charts.pop(idx)
        st.rerun()
else:
    st.info("No charts added yet. Use the Chart Library above or Auto-Build to populate your dashboard.")
