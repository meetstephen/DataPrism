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

# Direct upload option
with st.expander("\U0001F4C1 Upload your own file directly", expanded=False):
    adv_file = st.file_uploader(
        "Upload CSV, Excel, JSON, TSV, or Parquet",
        type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
        key="adv_file_upload",
        help="File will also be saved to your session for use on other pages.",
    )
    if adv_file is not None:
        from utils.data_loader import load_file_flexible
        loaded, err = load_file_flexible(adv_file)
        if err:
            st.error(err)
        elif loaded is not None:
            st.session_state.uploaded_df = loaded.copy()
            st.success(f"Loaded: {adv_file.name} ({len(loaded):,} rows)")

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
    "Clustering & Forecasting",
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


# --- EDA Auto-Charts ---
with tab6:
    st.markdown("### EDA Auto-Charts")
    st.markdown("Automatically generate exploratory data analysis charts based on data types.")

    import plotly.express as px

    if st.button("Generate Auto-Charts", type="primary", key="eda_auto"):
        numeric_cols_eda = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols_eda = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # Distribution plots for all numeric columns
        if numeric_cols_eda:
            st.markdown("#### Numeric Distributions")
            for i in range(0, len(numeric_cols_eda[:6]), 2):
                row_cols = st.columns(2)
                for j, col_widget in enumerate(row_cols):
                    idx = i + j
                    if idx < len(numeric_cols_eda[:6]):
                        with col_widget:
                            fig = create_histogram(df, numeric_cols_eda[idx], f"Distribution: {numeric_cols_eda[idx]}")
                            st.plotly_chart(fig, use_container_width=True)

        # Category counts
        if cat_cols_eda:
            st.markdown("#### Category Distributions")
            for col in cat_cols_eda[:4]:
                if df[col].nunique() <= 15:
                    counts = df[col].value_counts().head(10).reset_index()
                    counts.columns = [col, "Count"]
                    fig = create_bar_chart(counts, col, "Count", f"Top values: {col}")
                    st.plotly_chart(fig, use_container_width=True)

        # Pairwise scatter for top 3 numeric
        if len(numeric_cols_eda) >= 2:
            st.markdown("#### Pairwise Scatter")
            pairs = []
            for i in range(min(3, len(numeric_cols_eda))):
                for j in range(i + 1, min(3, len(numeric_cols_eda))):
                    pairs.append((numeric_cols_eda[i], numeric_cols_eda[j]))
            for x_col, y_col in pairs[:4]:
                fig = create_scatter_plot(df, x_col, y_col, f"{x_col} vs {y_col}")
                st.plotly_chart(fig, use_container_width=True)


# --- Statistical Tests ---
with tab7:
    st.markdown("### Statistical Tests")
    st.markdown("Run parametric and non-parametric statistical tests on your data.")

    from utils.statistics import run_ttest, run_chi_square, run_anova

    test_type = st.selectbox(
        "Test type:",
        ["T-Test (Independent)", "Chi-Square Test", "One-Way ANOVA"],
        key="stat_test_type",
    )

    if test_type == "T-Test (Independent)":
        numeric_cols_t = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols_t = df.select_dtypes(include=["object", "category"]).columns.tolist()

        if not numeric_cols_t or not cat_cols_t:
            st.info("Need at least one numeric and one categorical column for t-test.")
        else:
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                t_value_col = st.selectbox("Value column:", numeric_cols_t, key="ttest_val")
                t_group_col = st.selectbox("Group column:", cat_cols_t, key="ttest_group")
            with t_col2:
                groups = df[t_group_col].dropna().unique().tolist()[:20]
                t_group_a = st.selectbox("Group A:", groups, key="ttest_a")
                t_group_b = st.selectbox("Group B:", [g for g in groups if g != t_group_a], key="ttest_b")

            if st.button("Run T-Test", type="primary", key="run_ttest"):
                result = run_ttest(df, t_value_col, t_group_col, t_group_a, t_group_b)
                if "error" in result:
                    st.error(result["error"])
                else:
                    r1, r2, r3 = st.columns(3)
                    r1.metric("T-Statistic", f"{result['t_statistic']:.4f}")
                    r2.metric("P-Value", f"{result['p_value']:.6f}")
                    r3.metric("Significant?", "Yes" if result["significant"] else "No")
                    st.markdown(f"Mean of {t_group_a}: **{result['mean_a']:.4f}** (n={result['n_a']})")
                    st.markdown(f"Mean of {t_group_b}: **{result['mean_b']:.4f}** (n={result['n_b']})")

    elif test_type == "Chi-Square Test":
        cat_cols_chi = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if len(cat_cols_chi) < 2:
            st.info("Need at least 2 categorical columns for chi-square test.")
        else:
            chi_col1, chi_col2 = st.columns(2)
            with chi_col1:
                chi_a = st.selectbox("Column A:", cat_cols_chi, key="chi_a")
            with chi_col2:
                chi_b = st.selectbox("Column B:", [c for c in cat_cols_chi if c != chi_a], key="chi_b")
            if st.button("Run Chi-Square", type="primary", key="run_chi"):
                result = run_chi_square(df, chi_a, chi_b)
                if "error" in result:
                    st.error(result["error"])
                else:
                    r1, r2, r3 = st.columns(3)
                    r1.metric("Chi-Square", f"{result['chi2']:.4f}")
                    r2.metric("P-Value", f"{result['p_value']:.6f}")
                    r3.metric("Significant?", "Yes" if result["significant"] else "No")
                    st.caption(f"Degrees of freedom: {result['dof']}")

    elif test_type == "One-Way ANOVA":
        numeric_cols_a = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols_a = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not numeric_cols_a or not cat_cols_a:
            st.info("Need numeric and categorical columns for ANOVA.")
        else:
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                anova_val = st.selectbox("Value column:", numeric_cols_a, key="anova_val")
            with a_col2:
                anova_group = st.selectbox("Group column:", cat_cols_a, key="anova_group")
            if st.button("Run ANOVA", type="primary", key="run_anova"):
                result = run_anova(df, anova_val, anova_group)
                if "error" in result:
                    st.error(result["error"])
                else:
                    r1, r2, r3 = st.columns(3)
                    r1.metric("F-Statistic", f"{result['f_statistic']:.4f}")
                    r2.metric("P-Value", f"{result['p_value']:.6f}")
                    r3.metric("Significant?", "Yes" if result["significant"] else "No")
                    st.markdown(f"Groups: {result['n_groups']}")
                    st.json(result["group_means"])


# --- Regression ---
with tab8:
    st.markdown("### Regression Analysis")
    st.markdown("Run linear or logistic regression on your data.")

    from utils.statistics import run_linear_regression, run_logistic_regression

    reg_type = st.radio("Regression type:", ["Linear", "Logistic"], horizontal=True, key="reg_type")
    numeric_cols_reg = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols_reg) < 2:
        st.info("Need at least 2 numeric columns for regression.")
    else:
        reg_target = st.selectbox("Target (Y):", numeric_cols_reg, key="reg_target")
        reg_features = st.multiselect(
            "Features (X):",
            [c for c in numeric_cols_reg if c != reg_target],
            default=[c for c in numeric_cols_reg if c != reg_target][:3],
            key="reg_features",
        )

        if reg_features and st.button("Run Regression", type="primary", key="run_reg"):
            if reg_type == "Linear":
                result = run_linear_regression(df, reg_target, reg_features)
            else:
                result = run_logistic_regression(df, reg_target, reg_features)

            if "error" in result:
                st.error(result["error"])
            else:
                if reg_type == "Linear":
                    r1, r2, r3 = st.columns(3)
                    r1.metric("R-Squared", f"{result['r_squared']:.4f}")
                    r2.metric("Adj. R-Squared", f"{result['adj_r_squared']:.4f}")
                    r3.metric("Observations", result["n_observations"])
                else:
                    r1, r2 = st.columns(2)
                    r1.metric("Accuracy", f"{result['accuracy']:.4f}")
                    r2.metric("Observations", result["n_observations"])
                    st.markdown(f"Classes: {result.get('classes', [])}")

                st.markdown("#### Coefficients")
                coef_df = pd.DataFrame(
                    list(result["coefficients"].items()),
                    columns=["Feature", "Coefficient"]
                )
                st.dataframe(coef_df, use_container_width=True, hide_index=True)


# --- Clustering & Forecasting ---
with tab9:
    st.markdown("### Clustering & Forecasting")

    cluster_tab, forecast_tab = st.tabs(["K-Means Clustering", "Time Series Forecast"])

    with cluster_tab:
        st.markdown("#### K-Means Clustering")
        from utils.statistics import run_kmeans_clustering, ai_describe_clusters

        numeric_cols_km = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols_km) < 2:
            st.info("Need at least 2 numeric columns for clustering.")
        else:
            km_features = st.multiselect(
                "Features for clustering:",
                numeric_cols_km,
                default=numeric_cols_km[:3],
                key="km_features",
            )
            n_clusters = st.slider("Number of clusters:", 2, 10, 3, key="km_n_clusters")

            if km_features and st.button("Run K-Means", type="primary", key="run_kmeans"):
                result = run_kmeans_clustering(df, km_features, n_clusters)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.metric("Inertia", f"{result['inertia']:.2f}")
                    st.markdown("#### Cluster Centers")
                    centers_df = pd.DataFrame(result["centers"])
                    st.dataframe(centers_df, use_container_width=True, hide_index=True)

                    # Scatter plot of first two features colored by cluster
                    if len(km_features) >= 2:
                        plot_df = df[km_features].dropna().copy()
                        plot_df["Cluster"] = [str(l) for l in result["labels"]]
                        fig = create_scatter_plot(
                            plot_df, km_features[0], km_features[1],
                            "Cluster Visualization", color="Cluster"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # AI description
                    from utils.ai_client import get_api_key as _get_key
                    desc = ai_describe_clusters(result, api_key=_get_key())
                    st.markdown("#### Cluster Descriptions")
                    st.markdown(desc)

    with forecast_tab:
        st.markdown("#### Time Series Forecast (Holt-Winters)")
        from utils.forecasting import run_time_series_forecast, build_forecast_chart

        date_cols_fc = [c for c in df.columns if any(kw in c.lower() for kw in ["date", "year", "month", "time", "period"])]
        if not date_cols_fc:
            date_cols_fc = df.columns.tolist()
        numeric_cols_fc = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols_fc:
            st.info("Need at least one numeric column for forecasting.")
        else:
            fc_col1, fc_col2, fc_col3 = st.columns(3)
            with fc_col1:
                fc_date = st.selectbox("Date column:", date_cols_fc, key="fc_date")
            with fc_col2:
                fc_value = st.selectbox("Value column:", numeric_cols_fc, key="fc_value")
            with fc_col3:
                fc_periods = st.slider("Forecast periods:", 3, 36, 12, key="fc_periods")

            if st.button("Run Forecast", type="primary", key="run_forecast"):
                result = run_time_series_forecast(df, fc_date, fc_value, periods=fc_periods)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"Model: {result.get('model_summary', 'N/A')}")
                    if result.get("aic"):
                        st.caption(f"AIC: {result['aic']}")

                    fig = build_forecast_chart(result)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                    # Show forecast values
                    with st.expander("Forecast Values"):
                        st.dataframe(result["forecast"], use_container_width=True)
