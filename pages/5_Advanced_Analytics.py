"""
Advanced Analytics - Pivot tables, custom charts, and statistical tools.
"""

import streamlit as st
st.set_page_config(page_title="Advanced Analytics", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()
from utils.data_loader import ensure_builtin_data
ensure_builtin_data()

import pandas as pd
import numpy as np
from utils.data_generator import generate_dataset
from utils.visualizations import (
    create_bar_chart,
    create_scatter_plot,
    create_histogram,
    create_box_plot,
    create_line_chart,
    render_chart_with_table,
)
from utils.time_intelligence import (
    detect_date_columns,
    compute_time_intelligence,
    FREQ_CHOICES,
)

st.title("\U0001F527 Advanced Analytics")
st.markdown("Advanced analytical tools for deeper data exploration.")

# Load data
if "df" not in st.session_state:
    st.session_state.df = generate_dataset()

# Data source selection
data_source_options = ["Built-in Community College Data", "Uploaded Data"]
if "online_df" in st.session_state and st.session_state.online_df is not None:
    data_source_options.append("Online Data")
data_source = st.radio(
    "Select Data Source:",
    data_source_options,
    horizontal=True
)

if data_source == "Built-in Community College Data":
    df = st.session_state.df.copy()
elif data_source == "Online Data":
    if "online_df" in st.session_state and st.session_state.online_df is not None:
        df = st.session_state.online_df.copy()
    else:
        st.warning("No online data available. Using built-in dataset.")
        df = st.session_state.df.copy()
else:
    if "uploaded_df" in st.session_state:
        df = st.session_state.uploaded_df.copy()
    else:
        st.warning("No uploaded data available. Using built-in dataset.")
        df = st.session_state.df.copy()

st.info(f"Working with: {len(df)} rows, {len(df.columns)} columns")
st.markdown("---")

# Tab layout for different tools
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Pivot Table Builder",
    "Custom Chart Builder",
    "Statistical Summary",
    "Group By Analysis",
    "Time Intelligence"
])

# --- Pivot Table Builder ---
with tab1:
    st.markdown("### Pivot Table Builder")
    st.markdown("Create custom pivot tables to summarize your data.")

    pt_col1, pt_col2 = st.columns(2)

    all_columns = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    with pt_col1:
        index_col = st.selectbox("Index (Rows)", categorical_cols if categorical_cols else all_columns, key="pivot_index")
        values_col = st.selectbox("Values", numeric_cols if numeric_cols else all_columns, key="pivot_values")

    with pt_col2:
        columns_col = st.selectbox(
            "Columns (optional)",
            ["None"] + (categorical_cols if categorical_cols else all_columns),
            key="pivot_columns"
        )
        agg_func = st.selectbox("Aggregation", ["mean", "sum", "count", "min", "max"], key="pivot_agg")

    if st.button("Generate Pivot Table", key="gen_pivot"):
        with st.spinner("Generating pivot table..."):
            try:
                pivot_kwargs = {
                    "index": index_col,
                    "values": values_col,
                    "aggfunc": agg_func
                }
                if columns_col != "None":
                    pivot_kwargs["columns"] = columns_col

                pivot_table = pd.pivot_table(df, **pivot_kwargs)
                st.dataframe(pivot_table.round(2), use_container_width=True)

                # Download pivot table
                csv = pivot_table.to_csv()
                st.download_button("\U0001F4E5 Download Pivot Table", csv, "pivot_table.csv", "text/csv")

                # Show as chart if reasonable size
                if len(pivot_table) <= 20:
                    pivot_reset = pivot_table.reset_index()
                    if isinstance(pivot_reset.columns, pd.MultiIndex):
                        pivot_reset.columns = [
                            f"{c[0]}_{c[1]}" if c[1] else c[0]
                            for c in pivot_reset.columns
                        ]
                    st.markdown("**Pivot Table Visualization:**")
                    chart_cols = [c for c in pivot_reset.columns if c != index_col]
                    if chart_cols:
                        fig = create_bar_chart(
                            pivot_reset, index_col, chart_cols[0],
                            f"{agg_func.capitalize()} of {values_col} by {index_col}"
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        render_chart_with_table(
                            fig, pivot_reset, key="pivot_chart",
                            caption="Data behind the pivot visualization.",
                        )
            except Exception as e:
                st.error(f"Error creating pivot table: {str(e)}")

# --- Custom Chart Builder ---
with tab2:
    st.markdown("### Custom Chart Builder")
    st.markdown("Create your own visualizations by selecting axes and chart type.")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        x_axis = st.selectbox("X Axis", all_columns, key="chart_x")
        y_axis = st.selectbox("Y Axis", all_columns, key="chart_y", index=min(1, len(all_columns) - 1))

    with chart_col2:
        color_col = st.selectbox(
            "Color/Group (optional)",
            ["None"] + all_columns,
            key="chart_color"
        )
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar", "Scatter", "Line", "Box", "Histogram"],
            key="chart_type"
        )

    if x_axis == y_axis and chart_type != "Histogram":
        st.warning("X and Y axes are the same column. Please select different columns for a meaningful chart.")

    if st.button("Create Chart", key="gen_chart"):
        with st.spinner("Generating chart..."):
            try:
                color_param = color_col if color_col != "None" else None
                chart_data = None

                if chart_type == "Bar":
                    if color_param:
                        chart_df = df.groupby([x_axis, color_param])[y_axis].mean().reset_index()
                    else:
                        chart_df = df.groupby(x_axis)[y_axis].mean().reset_index()
                    fig = create_bar_chart(chart_df, x_axis, y_axis, f"{y_axis} by {x_axis}", color=color_param)
                    fig.update_layout(xaxis_tickangle=-45)
                    chart_data = chart_df

                elif chart_type == "Scatter":
                    fig = create_scatter_plot(df, x_axis, y_axis, f"{y_axis} vs {x_axis}", color=color_param)
                    scatter_cols = [c for c in [x_axis, y_axis, color_param] if c]
                    chart_data = df[scatter_cols]

                elif chart_type == "Line":
                    if color_param:
                        chart_df = df.groupby([x_axis, color_param])[y_axis].mean().reset_index()
                    else:
                        chart_df = df.groupby(x_axis)[y_axis].mean().reset_index()
                    fig = create_line_chart(
                        chart_df, x_axis, y_axis,
                        f"{y_axis} over {x_axis}",
                        color=color_param
                    )
                    chart_data = chart_df

                elif chart_type == "Box":
                    fig = create_box_plot(df, x_axis, y_axis, f"{y_axis} by {x_axis}")
                    chart_data = df[[x_axis, y_axis]]

                elif chart_type == "Histogram":
                    fig = create_histogram(df, x_axis, f"Distribution of {x_axis}")
                    chart_data = df[[x_axis]]

                render_chart_with_table(fig, chart_data, key="custom_chart")

            except Exception as e:
                st.error(f"Error creating chart: {str(e)}")

# --- Statistical Summary ---
with tab3:
    st.markdown("### Statistical Summary")
    st.markdown("Comprehensive descriptive statistics with percentiles.")

    if numeric_cols:
        desc = df[numeric_cols].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(3)
        st.dataframe(desc, use_container_width=True)

        st.markdown("#### Additional Statistics")
        additional = pd.DataFrame({
            "Column": numeric_cols,
            "Skewness": [df[col].skew() for col in numeric_cols],
            "Kurtosis": [df[col].kurtosis() for col in numeric_cols],
            "Coefficient of Variation": [
                df[col].std() / df[col].mean() if df[col].mean() != 0 else 0
                for col in numeric_cols
            ],
            "Range": [df[col].max() - df[col].min() for col in numeric_cols],
            "IQR": [df[col].quantile(0.75) - df[col].quantile(0.25) for col in numeric_cols]
        }).round(3)
        st.dataframe(additional, use_container_width=True)
    else:
        st.info("No numeric columns available for statistical analysis.")

    if categorical_cols:
        st.markdown("#### Categorical Column Summary")
        cat_stats = pd.DataFrame({
            "Column": categorical_cols,
            "Unique Values": [df[col].nunique() for col in categorical_cols],
            "Most Common": [df[col].mode().iloc[0] if not df[col].mode().empty else "N/A" for col in categorical_cols],
            "Most Common Freq": [df[col].value_counts().iloc[0] if not df[col].value_counts().empty else 0 for col in categorical_cols],
            "Least Common": [df[col].value_counts().index[-1] if not df[col].value_counts().empty else "N/A" for col in categorical_cols],
            "Least Common Freq": [df[col].value_counts().iloc[-1] if not df[col].value_counts().empty else 0 for col in categorical_cols]
        })
        st.dataframe(cat_stats, use_container_width=True)

# --- Group By Analysis ---
with tab4:
    st.markdown("### Group By Analysis")
    st.markdown("Aggregate data by categories to discover patterns.")

    gb_col1, gb_col2, gb_col3 = st.columns(3)

    with gb_col1:
        groupby_col = st.selectbox(
            "Group By Column",
            categorical_cols if categorical_cols else all_columns,
            key="gb_col"
        )

    with gb_col2:
        numeric_col = st.selectbox(
            "Numeric Column",
            numeric_cols if numeric_cols else all_columns,
            key="gb_num"
        )

    with gb_col3:
        gb_agg = st.selectbox(
            "Aggregation",
            ["mean", "sum", "count", "min", "max", "std", "median"],
            key="gb_agg"
        )

    if st.button("Run Group By", key="gen_groupby"):
        try:
            if gb_agg == "median":
                result = df.groupby(groupby_col)[numeric_col].median().reset_index()
            else:
                result = df.groupby(groupby_col)[numeric_col].agg(gb_agg).reset_index()

            result.columns = [groupby_col, f"{gb_agg}_{numeric_col}"]
            result = result.sort_values(f"{gb_agg}_{numeric_col}", ascending=False).round(2)

            st.dataframe(result, use_container_width=True)

            # Visualization
            if len(result) <= 30:
                fig = create_bar_chart(
                    result, groupby_col, f"{gb_agg}_{numeric_col}",
                    f"{gb_agg.capitalize()} of {numeric_col} by {groupby_col}"
                )
                fig.update_layout(xaxis_tickangle=-45)
                render_chart_with_table(
                    fig, result, key="groupby_chart",
                    caption="Aggregated values behind the chart.",
                )

        except Exception as e:
            st.error(f"Error in group by analysis: {str(e)}")


# --- Time Intelligence ---
with tab5:
    st.markdown("### Time Intelligence")
    st.markdown(
        "Track how a metric changes over time: period-over-period (e.g. MoM), "
        "year-over-year (YoY), and rolling averages."
    )

    ti_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_candidates = detect_date_columns(df)
    date_options = date_candidates if date_candidates else df.columns.tolist()

    if not ti_numeric_cols:
        st.info("Time intelligence needs at least one numeric value column.")
    else:
        if not date_candidates:
            st.warning(
                "No obvious date/time column was detected. Pick the column that "
                "represents time (a date, or a year/period column)."
            )

        ti_col1, ti_col2, ti_col3 = st.columns(3)
        with ti_col1:
            ti_date_col = st.selectbox("Date / time column", date_options, key="ti_date_col")
        with ti_col2:
            ti_value_col = st.selectbox("Value column", ti_numeric_cols, key="ti_value_col")
        with ti_col3:
            ti_agg = st.selectbox("Aggregation", ["sum", "mean", "min", "max", "count"], key="ti_agg")

        ti_col4, ti_col5 = st.columns(2)
        with ti_col4:
            ti_freq_label = st.selectbox("Period", list(FREQ_CHOICES.keys()), index=2, key="ti_freq")
        with ti_col5:
            ti_window = st.slider("Rolling average window (periods)", 2, 12, 3, key="ti_window")

        if st.button("Run Time Intelligence", type="primary", key="ti_run"):
            try:
                ti = compute_time_intelligence(
                    df,
                    ti_date_col,
                    ti_value_col,
                    freq=FREQ_CHOICES[ti_freq_label],
                    agg=ti_agg,
                    rolling_window=ti_window,
                )
                series = ti["series"]
                pop_label = ti["pop_label"]
                rolling_label = ti["rolling_label"]
                pop_col = f"{pop_label} %"

                if series.empty or len(series) < 2:
                    st.warning(
                        "Not enough time periods to compute trends. Try a coarser "
                        "period (e.g. Yearly) or check the date column."
                    )
                else:
                    latest = series.iloc[-1]
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric(f"Latest {ti_value_col}", f"{latest[ti_value_col]:,.2f}")
                    with m2:
                        pop_val = latest.get(pop_col)
                        st.metric(
                            f"{pop_label} change",
                            "N/A" if pd.isna(pop_val) else f"{pop_val:+.2f}%",
                        )
                    with m3:
                        yoy_val = latest.get("YoY %")
                        st.metric(
                            "YoY change",
                            "N/A" if pd.isna(yoy_val) else f"{yoy_val:+.2f}%",
                        )

                    # Value + rolling average overlay
                    line_long = series.melt(
                        id_vars=["Period"],
                        value_vars=[ti_value_col, rolling_label],
                        var_name="Series",
                        value_name="Value",
                    )
                    line_fig = create_line_chart(
                        line_long, "Period", "Value",
                        f"{ti_agg.capitalize()} of {ti_value_col} over time",
                        color="Series",
                    )
                    render_chart_with_table(
                        line_fig, series, key="ti_line",
                        caption="Period aggregates with change metrics and rolling average.",
                    )

                    # Period-over-period % change bar chart
                    change_df = series.dropna(subset=[pop_col])
                    if not change_df.empty:
                        change_fig = create_bar_chart(
                            change_df, "Period", pop_col,
                            f"{pop_label} % change in {ti_value_col}",
                        )
                        render_chart_with_table(
                            change_fig, change_df[["Period", pop_col, "YoY %"]],
                            key="ti_change",
                            caption="Period-over-period and year-over-year percentage change.",
                        )
            except Exception as e:
                st.error(f"Error computing time intelligence: {str(e)}")
