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
    create_line_chart
)
from utils.statistics import (
    run_ttest,
    run_chi_square,
    run_anova,
    run_linear_regression,
    run_logistic_regression,
    run_kmeans_clustering,
    ai_describe_clusters,
)
from utils.forecasting import run_time_series_forecast, build_forecast_chart
from utils.ai_client import get_api_key

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Pivot Table Builder",
    "Custom Chart Builder",
    "Statistical Summary",
    "Group By Analysis",
    "Time Intelligence",
    "EDA Auto-Charts",
    "Statistical Tests",
    "Regression",
    "Clustering & Forecasting"
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
                        st.plotly_chart(fig, use_container_width=True)
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

                if chart_type == "Bar":
                    if color_param:
                        chart_df = df.groupby([x_axis, color_param])[y_axis].mean().reset_index()
                    else:
                        chart_df = df.groupby(x_axis)[y_axis].mean().reset_index()
                    fig = create_bar_chart(chart_df, x_axis, y_axis, f"{y_axis} by {x_axis}", color=color_param)
                    fig.update_layout(xaxis_tickangle=-45)

                elif chart_type == "Scatter":
                    fig = create_scatter_plot(df, x_axis, y_axis, f"{y_axis} vs {x_axis}", color=color_param)

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

                elif chart_type == "Box":
                    fig = create_box_plot(df, x_axis, y_axis, f"{y_axis} by {x_axis}")

                elif chart_type == "Histogram":
                    fig = create_histogram(df, x_axis, f"Distribution of {x_axis}")

                st.plotly_chart(fig, use_container_width=True)

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
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error in group by analysis: {str(e)}")

# --- Time Intelligence ---
with tab5:
    st.markdown("### Time Intelligence")
    st.markdown("Analyze temporal patterns and seasonality in your data.")

    date_cols_ti = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    # Also detect date-like object columns
    for col in categorical_cols:
        try:
            parsed = pd.to_datetime(df[col], errors='coerce')
            if parsed.notna().sum() / max(len(df), 1) > 0.7:
                date_cols_ti.append(col)
        except Exception:
            pass

    if date_cols_ti:
        ti_date_col = st.selectbox("Date Column", date_cols_ti, key="ti_date")
        ti_value_col = st.selectbox("Value Column", numeric_cols if numeric_cols else all_columns, key="ti_value")

        if st.button("Analyze Time Patterns", key="ti_analyze"):
            try:
                temp_df = df[[ti_date_col, ti_value_col]].dropna().copy()
                temp_df[ti_date_col] = pd.to_datetime(temp_df[ti_date_col], errors='coerce')
                temp_df = temp_df.dropna().sort_values(ti_date_col)

                if len(temp_df) > 0:
                    fig = create_line_chart(temp_df, ti_date_col, ti_value_col, f"{ti_value_col} Over Time")
                    st.plotly_chart(fig, use_container_width=True)

                    # Basic time stats
                    st.markdown("**Time Range:**")
                    st.write(f"From {temp_df[ti_date_col].min()} to {temp_df[ti_date_col].max()}")
                    st.metric("Total Data Points", len(temp_df))
                else:
                    st.warning("No valid date-value pairs found.")
            except Exception as e:
                st.error(f"Error in time analysis: {str(e)}")
    else:
        st.info("No date columns detected. Upload data with date/time columns for time intelligence analysis.")

# --- EDA Auto-Charts ---
with tab6:
    st.markdown("### EDA Auto-Charts")
    st.markdown("Automatically generate one chart per column for quick exploration.")

    st.markdown("#### Univariate Analysis")
    chart_count = 0
    eda_cols = st.columns(2)

    for col in df.columns:
        if chart_count >= 20:
            st.info("Showing first 20 columns. Use other tabs for deeper analysis.")
            break
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                with eda_cols[chart_count % 2]:
                    fig = create_histogram(df, col, f"Distribution of {col}")
                    st.plotly_chart(fig, use_container_width=True)
                chart_count += 1
            elif df[col].nunique() < 50:
                with eda_cols[chart_count % 2]:
                    top_vals = df[col].value_counts().head(10).reset_index()
                    top_vals.columns = [col, "count"]
                    fig = create_bar_chart(top_vals, col, "count", f"Top 10 Values: {col}")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                chart_count += 1
            # Skip high-cardinality columns
        except Exception:
            pass

    if chart_count == 0:
        st.info("No suitable columns found for auto-charting.")

    st.markdown("---")
    st.markdown("#### Bivariate Analysis")
    bi_col1, bi_col2 = st.columns(2)
    with bi_col1:
        bi_x = st.selectbox("X Column", all_columns, key="eda_bi_x")
    with bi_col2:
        bi_y = st.selectbox("Y Column", all_columns, key="eda_bi_y", index=min(1, len(all_columns) - 1))

    if st.button("Generate Bivariate Chart", key="eda_bivariate"):
        try:
            x_is_numeric = pd.api.types.is_numeric_dtype(df[bi_x])
            y_is_numeric = pd.api.types.is_numeric_dtype(df[bi_y])

            if x_is_numeric and y_is_numeric:
                fig = create_scatter_plot(df, bi_x, bi_y, f"{bi_y} vs {bi_x}")
                st.plotly_chart(fig, use_container_width=True)
            elif x_is_numeric or y_is_numeric:
                # Grouped bar: aggregate numeric by categorical
                if x_is_numeric:
                    agg_df = df.groupby(bi_y)[bi_x].mean().reset_index()
                    agg_df.columns = [bi_y, bi_x]
                    fig = create_bar_chart(agg_df, bi_y, bi_x, f"Mean {bi_x} by {bi_y}")
                else:
                    agg_df = df.groupby(bi_x)[bi_y].mean().reset_index()
                    agg_df.columns = [bi_x, bi_y]
                    fig = create_bar_chart(agg_df, bi_x, bi_y, f"Mean {bi_y} by {bi_x}")
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Both categorical - cross-tabulation bar
                ct = pd.crosstab(df[bi_x], df[bi_y])
                if ct.size > 0:
                    st.dataframe(ct, use_container_width=True)
                else:
                    st.info("Unable to create a meaningful chart for these two categorical columns.")
        except Exception as e:
            st.error(f"Error in bivariate analysis: {str(e)}")

# --- Statistical Tests ---
with tab7:
    st.markdown("### Statistical Tests")
    st.markdown("Run hypothesis tests to determine if differences are statistically significant.")

    # T-Test Section
    st.markdown("#### Independent Samples T-Test")
    st.caption("Compare means of a numeric variable between two groups.")
    tt_col1, tt_col2 = st.columns(2)
    with tt_col1:
        tt_numeric = st.selectbox("Numeric Column", numeric_cols if numeric_cols else ["(none)"], key="tt_num")
        tt_group = st.selectbox("Grouping Column", categorical_cols if categorical_cols else ["(none)"], key="tt_grp")
    with tt_col2:
        if tt_group and tt_group != "(none)" and tt_group in df.columns:
            group_vals = df[tt_group].dropna().unique().tolist()
        else:
            group_vals = []
        tt_group_a = st.selectbox("Group A", group_vals if group_vals else ["(none)"], key="tt_ga")
        tt_group_b = st.selectbox("Group B", group_vals if group_vals else ["(none)"], key="tt_gb",
                                  index=min(1, len(group_vals) - 1) if len(group_vals) > 1 else 0)

    if st.button("Run T-Test", key="run_ttest"):
        if tt_numeric == "(none)" or tt_group == "(none)":
            st.warning("Please select valid columns.")
        else:
            try:
                result = run_ttest(df, tt_numeric, tt_group, tt_group_a, tt_group_b)
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("T-Statistic", result["t_stat"] if result["t_stat"] is not None else "N/A")
                with col_b:
                    st.metric("P-Value", result["p_value"] if result["p_value"] is not None else "N/A")
                with col_c:
                    sig = "Yes" if result["p_value"] is not None and result["p_value"] < 0.05 else "No"
                    st.metric("Significant (p<0.05)?", sig)
                st.info(result["verdict"])
            except Exception as e:
                st.error(f"T-Test failed: {str(e)}")

    st.markdown("---")

    # Chi-Square Section
    st.markdown("#### Chi-Square Test of Independence")
    st.caption("Test if two categorical variables are related.")
    chi_col1, chi_col2 = st.columns(2)
    with chi_col1:
        chi_a = st.selectbox("Categorical Column A", categorical_cols if categorical_cols else ["(none)"], key="chi_a")
    with chi_col2:
        chi_b = st.selectbox("Categorical Column B", categorical_cols if categorical_cols else ["(none)"], key="chi_b",
                             index=min(1, len(categorical_cols) - 1) if len(categorical_cols) > 1 else 0)

    if st.button("Run Chi-Square Test", key="run_chi"):
        if chi_a == "(none)" or chi_b == "(none)":
            st.warning("Please select valid categorical columns.")
        else:
            try:
                result = run_chi_square(df, chi_a, chi_b)
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Chi-Square", result["chi2"] if result["chi2"] is not None else "N/A")
                with col_b:
                    st.metric("P-Value", result["p_value"] if result["p_value"] is not None else "N/A")
                with col_c:
                    st.metric("Degrees of Freedom", result["dof"] if result["dof"] is not None else "N/A")
                with col_d:
                    sig = "Yes" if result["p_value"] is not None and result["p_value"] < 0.05 else "No"
                    st.metric("Significant?", sig)
                st.info(result["verdict"])
            except Exception as e:
                st.error(f"Chi-Square test failed: {str(e)}")

    st.markdown("---")

    # ANOVA Section
    st.markdown("#### One-Way ANOVA")
    st.caption("Test if the mean of a numeric variable differs across multiple groups.")
    an_col1, an_col2 = st.columns(2)
    with an_col1:
        an_numeric = st.selectbox("Numeric Column", numeric_cols if numeric_cols else ["(none)"], key="an_num")
    with an_col2:
        an_group = st.selectbox("Grouping Column", categorical_cols if categorical_cols else ["(none)"], key="an_grp")

    if st.button("Run ANOVA", key="run_anova"):
        if an_numeric == "(none)" or an_group == "(none)":
            st.warning("Please select valid columns.")
        else:
            try:
                result = run_anova(df, an_numeric, an_group)
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("F-Statistic", result["f_stat"] if result["f_stat"] is not None else "N/A")
                with col_b:
                    st.metric("P-Value", result["p_value"] if result["p_value"] is not None else "N/A")
                with col_c:
                    sig = "Yes" if result["p_value"] is not None and result["p_value"] < 0.05 else "No"
                    st.metric("Significant?", sig)
                st.info(result["verdict"])
            except Exception as e:
                st.error(f"ANOVA failed: {str(e)}")

# --- Regression ---
with tab8:
    st.markdown("### Regression Analysis")
    st.markdown("Fit regression models to understand relationships between variables.")

    # Linear Regression
    st.markdown("#### Linear Regression")
    st.caption("Predict a continuous numeric outcome from one or more features.")
    lr_col1, lr_col2 = st.columns(2)
    with lr_col1:
        lr_x_cols = st.multiselect("Feature Columns (X)", numeric_cols, key="lr_x",
                                    default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols[:1])
    with lr_col2:
        lr_y_col = st.selectbox("Target Column (Y)", numeric_cols if numeric_cols else ["(none)"], key="lr_y",
                                index=min(len(numeric_cols) - 1, 2) if len(numeric_cols) > 2 else 0)

    if st.button("Run Linear Regression", key="run_lr"):
        if not lr_x_cols or lr_y_col == "(none)":
            st.warning("Please select at least one feature column and a target column.")
        else:
            try:
                result = run_linear_regression(df, lr_x_cols, lr_y_col)
                if result["r_squared"] is not None:
                    st.metric("R-Squared", result["r_squared"])
                    st.markdown("**Coefficients:**")
                    st.dataframe(result["coefficients_df"], use_container_width=True)

                    # Scatter plot with predictions (for single X)
                    if len(lr_x_cols) == 1 and len(result["predictions"]) > 0:
                        import plotly.graph_objects as go
                        clean_df_lr = df[lr_x_cols + [lr_y_col]].dropna()
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=clean_df_lr[lr_x_cols[0]], y=clean_df_lr[lr_y_col],
                            mode="markers", name="Actual", marker=dict(color="#00D4FF", opacity=0.6)
                        ))
                        fig.add_trace(go.Scatter(
                            x=clean_df_lr[lr_x_cols[0]], y=result["predictions"],
                            mode="lines", name="Regression Line", line=dict(color="#EF4444", width=2)
                        ))
                        fig.update_layout(title=f"Linear Regression: {lr_y_col} vs {lr_x_cols[0]}",
                                          xaxis_title=lr_x_cols[0], yaxis_title=lr_y_col,
                                          template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for regression (need at least 3 complete rows).")
            except Exception as e:
                st.error(f"Linear regression failed: {str(e)}")

    st.markdown("---")

    # Logistic Regression
    st.markdown("#### Logistic Regression")
    st.caption("Classify a categorical/binary outcome from numeric features.")
    log_col1, log_col2 = st.columns(2)
    with log_col1:
        log_x_cols = st.multiselect("Feature Columns (X)", numeric_cols, key="log_x",
                                     default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols[:1])
    with log_col2:
        # Allow selection of any column for Y (binary/categorical target)
        log_y_options = categorical_cols + [c for c in numeric_cols if df[c].nunique() <= 10]
        log_y_col = st.selectbox("Target Column (Y)", log_y_options if log_y_options else ["(none)"], key="log_y")

    if st.button("Run Logistic Regression", key="run_logr"):
        if not log_x_cols or log_y_col == "(none)":
            st.warning("Please select feature columns and a target.")
        else:
            try:
                result = run_logistic_regression(df, log_x_cols, log_y_col)
                if result["accuracy"] is not None:
                    st.metric("Accuracy", result["accuracy"])
                    st.markdown("**Coefficients:**")
                    st.dataframe(result["coefficients_df"], use_container_width=True)
                    st.markdown("**Classification Report:**")
                    st.code(result["report"])
                else:
                    st.warning("Insufficient data for logistic regression (need at least 5 complete rows).")
            except Exception as e:
                st.error(f"Logistic regression failed: {str(e)}")

# --- Clustering & Forecasting ---
with tab9:
    st.markdown("### Clustering & Forecasting")
    st.markdown("Discover natural groups in your data and forecast future values.")

    # K-Means Clustering
    st.markdown("#### K-Means Clustering")
    st.caption("Group similar data points together based on numeric features.")

    km_cols = st.multiselect("Select Numeric Columns (at least 2)",
                              numeric_cols, key="km_cols",
                              default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols[:2])
    km_max_k = st.slider("Maximum K (clusters to try)", min_value=3, max_value=15, value=10, key="km_max_k")

    if st.button("Run K-Means Clustering", key="run_kmeans"):
        if len(km_cols) < 2:
            st.warning("Please select at least 2 numeric columns for clustering.")
        else:
            try:
                result = run_kmeans_clustering(df, km_cols, max_k=km_max_k)
                if len(result["inertias"]) > 0:
                    st.markdown(f"**Optimal K (elbow method):** {result['optimal_k']}")

                    # Elbow chart
                    import plotly.graph_objects as go
                    k_range = list(range(2, 2 + len(result["inertias"])))
                    fig_elbow = go.Figure()
                    fig_elbow.add_trace(go.Scatter(
                        x=k_range, y=result["inertias"],
                        mode="lines+markers", name="Inertia",
                        line=dict(color="#00D4FF", width=2),
                        marker=dict(size=8)
                    ))
                    fig_elbow.update_layout(title="Elbow Chart: K vs Inertia",
                                            xaxis_title="Number of Clusters (K)",
                                            yaxis_title="Inertia",
                                            template="plotly_white")
                    st.plotly_chart(fig_elbow, use_container_width=True)

                    # Cluster statistics
                    st.markdown("**Per-Cluster Statistics (mean values):**")
                    st.dataframe(result["cluster_stats"], use_container_width=True)

                    # AI cluster descriptions
                    api_key = get_api_key()
                    if api_key:
                        with st.spinner("Generating AI cluster descriptions..."):
                            desc_text, desc_err = ai_describe_clusters(result["cluster_stats"], api_key)
                            if desc_text:
                                st.markdown("**AI Cluster Descriptions:**")
                                st.markdown(desc_text)
                            elif desc_err:
                                st.warning(f"AI description unavailable: {desc_err}")
                    else:
                        st.info("Add a Gemini API key for AI-generated cluster descriptions.")
                else:
                    st.warning("Insufficient data for clustering (need at least 4 rows with no missing values).")
            except Exception as e:
                st.error(f"Clustering failed: {str(e)}")

    st.markdown("---")

    # Time Series Forecasting
    st.markdown("#### Time Series Forecasting")
    st.caption("Forecast future values using Holt-Winters exponential smoothing.")

    # Detect date columns
    date_cols_fc = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    for col in categorical_cols:
        try:
            parsed = pd.to_datetime(df[col], errors='coerce')
            if parsed.notna().sum() / max(len(df), 1) > 0.7:
                if col not in date_cols_fc:
                    date_cols_fc.append(col)
        except Exception:
            pass

    if date_cols_fc and numeric_cols:
        fc_col1, fc_col2 = st.columns(2)
        with fc_col1:
            fc_date_col = st.selectbox("Date Column", date_cols_fc, key="fc_date")
            fc_value_col = st.selectbox("Value Column", numeric_cols, key="fc_value")
        with fc_col2:
            fc_periods = st.slider("Forecast Periods", min_value=1, max_value=36, value=12, key="fc_periods")
            fc_freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "MS", "Quarterly": "QS", "Yearly": "YS"}
            fc_freq_label = st.selectbox("Frequency", list(fc_freq_map.keys()), index=2, key="fc_freq")
            fc_freq = fc_freq_map[fc_freq_label]

        if st.button("Run Forecast", key="run_forecast"):
            try:
                with st.spinner("Building forecast model..."):
                    result = run_time_series_forecast(df, fc_date_col, fc_value_col,
                                                      periods=fc_periods, freq=fc_freq)
                    if not result["forecast_df"].empty:
                        fig = build_forecast_chart(result)
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("**Forecast Values:**")
                        st.dataframe(result["forecast_df"].round(2), use_container_width=True)
                    else:
                        st.warning("Insufficient data to generate a forecast. Need at least 4 data points after resampling.")
            except Exception as e:
                st.error(f"Forecasting failed: {str(e)}")
    else:
        st.info("No date columns detected or no numeric columns available. Upload data with date and numeric columns for forecasting.")
