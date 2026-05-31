"""Dashboard Builder - KPI cards, chart library, auto-build, global filters."""
import streamlit as st
st.set_page_config(page_title="Dashboard Builder", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import ensure_builtin_data, init_all_session_state
from utils.dashboard_builder import (
    detect_kpi_columns,
    build_kpi_card_data,
    auto_build_dashboard,
    CHART_REGISTRY,
)
from utils.visualizations import (
    create_bar_chart,
    create_line_chart,
    create_scatter_plot,
    create_histogram,
    create_box_plot,
    create_heatmap,
)

init_all_session_state()

st.title("\U0001F4CA Dashboard Builder")
st.markdown("Build interactive dashboards with KPI cards, chart library, and auto-build capabilities.")

# Data source selection
st.markdown("### Select Data Source")
sources = ["Built-in Community College Data"]
if st.session_state.get("uploaded_df") is not None:
    sources.append("Uploaded Data")
if st.session_state.get("working_df") is not None:
    sources.append("Cleaned Data")
if st.session_state.get("online_df") is not None:
    sources.append("Online Data")

data_source = st.radio("Choose data:", sources, horizontal=True, key="dash_source")

df = None
if data_source == "Built-in Community College Data":
    df = ensure_builtin_data()
elif data_source == "Uploaded Data":
    df = st.session_state.get("uploaded_df")
elif data_source == "Cleaned Data":
    df = st.session_state.get("working_df")
elif data_source == "Online Data":
    df = st.session_state.get("online_df")

# Direct upload option — so users can bring their own data without visiting another page
with st.expander("\U0001F4C1 Upload your own file directly", expanded=(df is None)):
    dash_upload_col1, dash_upload_col2 = st.columns([3, 2])
    with dash_upload_col1:
        dash_file = st.file_uploader(
            "Upload CSV, Excel, JSON, TSV, or Parquet",
            type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
            key="dash_file_upload",
            help="File will also be saved to your session for use on other pages.",
        )
    with dash_upload_col2:
        st.markdown("")
        st.markdown("")
        st.caption("Or paste CSV/TSV text below:")
        dash_paste = st.text_area(
            "Paste data",
            height=100,
            key="dash_paste",
            placeholder="col1,col2,col3\n1,a,100\n2,b,200",
            label_visibility="collapsed",
        )

    if dash_file is not None:
        from utils.data_loader import load_file_flexible
        loaded, err = load_file_flexible(dash_file)
        if err:
            st.error(err)
        elif loaded is not None:
            df = loaded
            st.session_state.uploaded_df = df.copy()
            st.success(f"Loaded: {dash_file.name} ({len(df):,} rows)")
    elif dash_paste and dash_paste.strip():
        from utils.data_loader import parse_pasted_csv
        loaded, err = parse_pasted_csv(dash_paste)
        if err:
            st.error(err)
        elif loaded is not None:
            df = loaded
            st.session_state.uploaded_df = df.copy()
            st.success(f"Loaded pasted data ({len(df):,} rows)")

if df is None or df.empty:
    st.warning("No data available. Upload a file above, or load data from another page.")
    try:
        st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Go to Upload & Analyze", icon="\U0001F4C1")
    except Exception:
        pass
    st.stop()

# Global Filters
st.markdown("---")
with st.expander("\U0001F50D Global Filters", expanded=False):
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    filter_values = {}
    if cat_cols:
        filter_cols = st.multiselect("Filter by columns:", cat_cols, key="dash_filter_cols")
        for col in filter_cols:
            unique_vals = df[col].dropna().unique().tolist()
            selected = st.multiselect(f"Values for '{col}':", unique_vals, default=unique_vals, key=f"dash_filt_{col}")
            filter_values[col] = selected

    # Apply filters
    filtered_df = df.copy()
    for col, vals in filter_values.items():
        if vals:
            filtered_df = filtered_df[filtered_df[col].isin(vals)]

    if len(filtered_df) < len(df):
        st.info(f"Showing {len(filtered_df):,} of {len(df):,} rows after filtering.")
    df = filtered_df

st.markdown("---")

# Tab layout
tab_auto, tab_kpi, tab_charts = st.tabs(["\U0001F680 Auto-Build", "\U0001F4C8 KPI Cards", "\U0001F3A8 Chart Library"])

# Auto-Build Tab
with tab_auto:
    st.markdown("### Auto-Build Dashboard")
    st.markdown("Automatically generate a dashboard based on your dataset structure.")

    if st.button("Auto-Build Dashboard", type="primary", key="auto_build_btn"):
        with st.spinner("Building dashboard..."):
            dashboard = auto_build_dashboard(df)
            st.session_state["_auto_dashboard"] = dashboard

    dashboard = st.session_state.get("_auto_dashboard")
    if dashboard:
        # KPI Row
        kpis = dashboard.get("kpis", [])
        if kpis:
            kpi_cols = st.columns(len(kpis))
            for i, kpi in enumerate(kpis):
                with kpi_cols[i]:
                    st.metric(kpi["label"], f"{kpi['value']:,.2f}" if isinstance(kpi["value"], float) else f"{kpi['value']:,}")

        # Charts
        charts = dashboard.get("charts", [])
        for i in range(0, len(charts), 2):
            chart_row = st.columns(2)
            for j, col in enumerate(chart_row):
                idx = i + j
                if idx >= len(charts):
                    break
                chart_cfg = charts[idx]
                with col:
                    st.markdown(f"**{chart_cfg['title']}**")
                    try:
                        _render_auto_chart(df, chart_cfg)
                    except Exception as e:
                        st.error(f"Chart error: {str(e)}")


def _render_auto_chart(df, chart_cfg):
    """Render a chart from auto-build configuration."""
    chart_type = chart_cfg["type"]
    config = chart_cfg["config"]

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if chart_type == "histogram":
        x = config.get("x")
        if x and x in df.columns:
            fig = create_histogram(df, x, chart_cfg["title"])
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "bar":
        x = config.get("x")
        if x and x in df.columns:
            if config.get("y") == "count":
                counts = df[x].value_counts().head(15).reset_index()
                counts.columns = [x, "Count"]
                fig = create_bar_chart(counts, x, "Count", chart_cfg["title"])
            else:
                y = config.get("y", numeric_cols[0] if numeric_cols else x)
                chart_df = df.groupby(x)[y].mean().reset_index()
                fig = create_bar_chart(chart_df, x, y, chart_cfg["title"])
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "scatter":
        x = config.get("x")
        y = config.get("y")
        if x and y and x in df.columns and y in df.columns:
            fig = create_scatter_plot(df, x, y, chart_cfg["title"])
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "line":
        x = config.get("x")
        y = config.get("y")
        if x and y and x in df.columns and y in df.columns:
            chart_df = df.groupby(x)[y].mean().reset_index()
            fig = create_line_chart(chart_df, x, y, chart_cfg["title"])
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "heatmap":
        cols = config.get("columns", numeric_cols[:8])
        available_cols = [c for c in cols if c in df.columns]
        if len(available_cols) >= 2:
            corr = df[available_cols].corr()
            fig = create_heatmap(corr, chart_cfg["title"])
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "box":
        x = config.get("x")
        y = config.get("y")
        if x and y and x in df.columns and y in df.columns:
            fig = create_box_plot(df, x, y, chart_cfg["title"])
            st.plotly_chart(fig, use_container_width=True)


# KPI Cards Tab
with tab_kpi:
    st.markdown("### KPI Card Builder")
    st.markdown("Select metrics and build custom KPI cards.")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        st.info("No numeric columns available for KPI cards.")
    else:
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            kpi_column = st.selectbox("Metric column:", numeric_cols, key="kpi_col_select")
        with kpi_col2:
            kpi_agg = st.selectbox("Aggregation:", ["mean", "sum", "count", "max", "min"], key="kpi_agg_select")
        with kpi_col3:
            st.markdown("")
            st.markdown("")
            show_kpi = st.button("Show KPI", type="primary", key="show_kpi_btn")

        if show_kpi:
            kpi_data = build_kpi_card_data(df, kpi_column, kpi_agg)
            if kpi_data:
                delta_str = f"{kpi_data['delta']:+.1f}%" if kpi_data.get("delta") is not None else None
                st.metric(kpi_data["label"], f"{kpi_data['value']:,.2f}", delta=delta_str)

        # Auto-detected KPIs
        st.markdown("#### Auto-Detected KPIs")
        auto_kpis = detect_kpi_columns(df)
        if auto_kpis:
            auto_cols = st.columns(len(auto_kpis))
            for i, kpi in enumerate(auto_kpis):
                with auto_cols[i]:
                    if kpi.get("format") == "integer":
                        st.metric(kpi["label"], f"{kpi['value']:,}")
                    elif kpi.get("format") == "percent":
                        st.metric(kpi["label"], f"{kpi['value']}%")
                    else:
                        st.metric(kpi["label"], f"{kpi['value']:,.2f}")

# Chart Library Tab
with tab_charts:
    st.markdown("### Chart Library")
    st.markdown(f"Choose from {len(CHART_REGISTRY)} chart types to visualize your data.")

    all_columns = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Chart type selector
    chart_type_labels = [f"{info['icon']} {info['label']}" for info in CHART_REGISTRY.values()]
    chart_type_keys = list(CHART_REGISTRY.keys())

    selected_label = st.selectbox("Chart Type:", chart_type_labels, key="chart_lib_type")
    selected_type = chart_type_keys[chart_type_labels.index(selected_label)]

    # Axis selectors
    lib_col1, lib_col2 = st.columns(2)
    with lib_col1:
        x_axis = st.selectbox("X Axis:", all_columns, key="chart_lib_x")
    with lib_col2:
        y_axis = st.selectbox("Y Axis:", all_columns, key="chart_lib_y", index=min(1, len(all_columns) - 1))

    if st.button("Create Chart", type="primary", key="chart_lib_create"):
        try:
            if selected_type == "bar":
                chart_df = df.groupby(x_axis)[y_axis].mean().reset_index() if x_axis != y_axis else df
                fig = create_bar_chart(chart_df, x_axis, y_axis, f"{y_axis} by {x_axis}")
            elif selected_type == "line":
                chart_df = df.groupby(x_axis)[y_axis].mean().reset_index() if x_axis != y_axis else df
                fig = create_line_chart(chart_df, x_axis, y_axis, f"{y_axis} over {x_axis}")
            elif selected_type == "scatter":
                fig = create_scatter_plot(df, x_axis, y_axis, f"{x_axis} vs {y_axis}")
            elif selected_type == "histogram":
                fig = create_histogram(df, x_axis, f"Distribution of {x_axis}")
            elif selected_type == "box":
                fig = create_box_plot(df, x_axis, y_axis, f"{y_axis} by {x_axis}")
            elif selected_type == "pie":
                counts = df[x_axis].value_counts().head(10).reset_index()
                counts.columns = [x_axis, "Count"]
                fig = px.pie(counts, names=x_axis, values="Count", title=f"Distribution of {x_axis}", hole=0.4)
                fig.update_layout(template="plotly_dark", height=400)
            elif selected_type == "heatmap":
                avail_num = [c for c in numeric_cols if c in df.columns]
                if len(avail_num) >= 2:
                    corr = df[avail_num[:10]].corr()
                    fig = create_heatmap(corr, "Correlation Heatmap")
                else:
                    st.error("Need at least 2 numeric columns for heatmap.")
                    fig = None
            elif selected_type == "area":
                chart_df = df.groupby(x_axis)[y_axis].mean().reset_index() if x_axis != y_axis else df
                fig = px.area(chart_df, x=x_axis, y=y_axis, title=f"{y_axis} area over {x_axis}")
                fig.update_layout(template="plotly_dark", height=400)
            elif selected_type == "violin":
                fig = px.violin(df, x=x_axis, y=y_axis, title=f"{y_axis} violin by {x_axis}")
                fig.update_layout(template="plotly_dark", height=400)
            elif selected_type == "treemap":
                counts = df[x_axis].value_counts().head(20).reset_index()
                counts.columns = [x_axis, "Count"]
                fig = px.treemap(counts, path=[x_axis], values="Count", title=f"Treemap of {x_axis}")
                fig.update_layout(template="plotly_dark", height=400)
            elif selected_type == "funnel":
                counts = df[x_axis].value_counts().head(8).reset_index()
                counts.columns = [x_axis, "Count"]
                fig = px.funnel(counts, x="Count", y=x_axis, title=f"Funnel of {x_axis}")
                fig.update_layout(template="plotly_dark", height=400)
            else:
                fig = None

            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
