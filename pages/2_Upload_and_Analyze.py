"""
Upload and Analyze - Universal dataset analysis tool.
"""

import streamlit as st
st.set_page_config(page_title="Upload & Analyze", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_sidebar_nav
inject_global_css()
render_sidebar_nav()

import pandas as pd
import numpy as np
from utils.visualizations import (
    create_histogram,
    create_bar_chart,
    create_heatmap,
    create_box_plot
)
from utils.ai_insights import generate_data_quality_report
from utils.exporters import render_export_buttons
from utils.supabase_client import is_configured
from utils import database as db
from utils.data_loader import (
    SAMPLE_DATASETS, load_sample_dataset, parse_pasted_csv, load_file_flexible,
)

st.title("\U0001F4C1 Upload & Analyze Your Data")
st.markdown(
    "Upload a CSV, Excel, JSON, TSV, or Parquet file — **including Power BI exported data** — to get "
    "instant automated analysis, visualizations, and data-quality insights."
)

# --- Tabs for data input methods ---
input_tab1, input_tab2, input_tab3 = st.tabs([
    "\U0001F4C1 Upload File", "\U0001F4CB Paste Data", "\U0001F4E6 Sample Datasets"
])

df = None

with input_tab1:
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
        help="Upload CSV, Excel, JSON, TSV, or Parquet. Power BI: export as CSV/Excel.",
    )
    if uploaded_file is not None:
        MAX_FILE_SIZE_MB = 50
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"File size ({file_size_mb:.1f} MB) exceeds {MAX_FILE_SIZE_MB} MB limit.")
        else:
            loaded_df, err = load_file_flexible(uploaded_file)
            if err:
                st.error(err)
            elif loaded_df is not None:
                df = loaded_df
                st.success(f"File loaded: {uploaded_file.name}")

with input_tab2:
    st.markdown("Paste CSV or tab-separated data below:")
    pasted_text = st.text_area(
        "Paste your data here",
        height=200,
        placeholder="col1,col2,col3\nval1,val2,val3\n...",
        key="paste_data_input",
    )
    if st.button("Parse Pasted Data", key="parse_paste_btn"):
        parsed_df, err = parse_pasted_csv(pasted_text)
        if err:
            st.error(err)
        elif parsed_df is not None:
            df = parsed_df
            st.success(f"Parsed {len(df):,} rows x {len(df.columns)} columns")

with input_tab3:
    st.markdown("Load a built-in sample dataset:")
    sample_name = st.selectbox(
        "Choose sample dataset:",
        list(SAMPLE_DATASETS.keys()),
        format_func=lambda x: f"{x} - {SAMPLE_DATASETS[x]['description']}",
        key="sample_ds_select",
    )
    if st.button("Load Sample Dataset", type="primary", key="load_sample_btn"):
        sample_df = load_sample_dataset(sample_name)
        if sample_df is not None:
            df = sample_df
            st.success(f"Loaded '{sample_name}' ({len(df):,} rows x {len(df.columns)} columns)")
        else:
            st.error("Could not load sample dataset.")

# If we got data from any source, process it
if df is not None:
    # Edge case: empty dataframe
    if len(df) == 0:
        st.warning("The uploaded file contains 0 rows. Please upload a file with data.")
        st.stop()

    # Edge case: single column
    single_column = len(df.columns) == 1

    # Row count warning
    MAX_ROWS_WARNING = 100_000
    if len(df) > MAX_ROWS_WARNING:
        st.warning(
            f"The dataset contains {len(df):,} rows, which exceeds {MAX_ROWS_WARNING:,}. "
            "Performance may be affected. Consider filtering or sampling the data."
        )

    # Store in session state for use in other pages
    st.session_state.uploaded_df = df
    from utils.persistence import save_session_state
    save_session_state()

    # Multi-format export for the loaded data
    st.markdown("**Download data:**")
    render_export_buttons(df, base_filename="analyzed_data", key_prefix="upload_export")

    # Optional: save to cloud (Supabase)
    if is_configured():
        with st.expander("\u2601\uFE0F Save this dataset to the cloud"):
            cloud_name = st.text_input("Save as name", value="my_dataset", key="upload_cloud_name")
            if st.button("Save to cloud", key="upload_cloud_save"):
                ok, msg = db.save_dataset(cloud_name.strip(), df)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    try:
                        from utils.auth import log_user_activity
                        log_user_activity("dataset_uploaded", details=cloud_name.strip(), page="upload")
                    except Exception:
                        pass
    else:
        st.caption(
            "\u2601\uFE0F Tip: connect a database (see SUPABASE_SETUP.md) to save datasets to the cloud."
        )

    # Data Preview
    st.markdown("### Data Preview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    st.dataframe(df.head(10), use_container_width=True)

    # Column type detection
    st.markdown("### Column Types")
    type_info = pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str).values,
        "Non-Null": df.notna().sum().values,
        "Unique Values": [df[col].nunique() for col in df.columns]
    })
    st.dataframe(type_info, use_container_width=True)

    # Summary statistics
    st.markdown("### Summary Statistics")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if numeric_cols:
        st.markdown("**Numeric Columns**")
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)

    if categorical_cols:
        st.markdown("**Categorical Columns**")
        cat_summary = pd.DataFrame({
            "Column": categorical_cols,
            "Unique": [df[col].nunique() for col in categorical_cols],
            "Most Common": [df[col].mode().iloc[0] if not df[col].mode().empty else "N/A" for col in categorical_cols],
            "Frequency": [df[col].value_counts().iloc[0] if not df[col].value_counts().empty else 0 for col in categorical_cols]
        })
        st.dataframe(cat_summary, use_container_width=True)

    st.markdown("---")

    # Automatic Chart Suggestions
    st.markdown("### Automatic Visualizations")

    with st.spinner("Generating visualizations..."):
        # Histograms for numeric columns
        if numeric_cols:
            st.markdown("#### Distributions (Numeric Columns)")
            hist_cols = st.columns(min(len(numeric_cols), 2))
            for idx, col in enumerate(numeric_cols[:4]):
                with hist_cols[idx % 2]:
                    fig = create_histogram(df, col, f"Distribution of {col}")
                    st.plotly_chart(fig, use_container_width=True)

        # Bar charts for categorical columns with few unique values
        low_cardinality = [c for c in categorical_cols if df[c].nunique() <= 15]
        if low_cardinality:
            st.markdown("#### Category Distributions")
            bar_cols = st.columns(min(len(low_cardinality), 2))
            for idx, col in enumerate(low_cardinality[:4]):
                with bar_cols[idx % 2]:
                    value_counts = df[col].value_counts().reset_index()
                    value_counts.columns = [col, "Count"]
                    fig = create_bar_chart(value_counts, col, "Count", f"Distribution of {col}")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

        # Correlation Heatmap
        if len(numeric_cols) >= 2 and not single_column:
            st.markdown("### Correlation Analysis")
            corr_matrix = df[numeric_cols].corr()
            fig = create_heatmap(corr_matrix, "Correlation Heatmap")
            st.plotly_chart(fig, use_container_width=True)
        elif single_column:
            st.info("Only 1 column available. Correlation analysis requires at least 2 numeric columns.")

    # Missing Data Analysis
    st.markdown("### Missing Data Analysis")
    missing = df.isnull().sum()
    missing_df = pd.DataFrame({
        "Column": missing.index,
        "Missing Count": missing.values,
        "Missing Percentage": (missing.values / len(df) * 100).round(2)
    })
    missing_df = missing_df[missing_df["Missing Count"] > 0]

    if len(missing_df) > 0:
        st.dataframe(missing_df, use_container_width=True)
        fig = create_bar_chart(
            missing_df, "Column", "Missing Percentage",
            "Missing Values by Column (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No missing values found in the dataset!")

    # Data Quality Report
    st.markdown("### Data Quality Report")
    with st.spinner("Generating data quality report..."):
        quality_report = generate_data_quality_report(df)

        qual_col1, qual_col2, qual_col3 = st.columns(3)
        with qual_col1:
            st.metric("Completeness", f"{quality_report['completeness_score']}%")
        with qual_col2:
            st.metric("Duplicate Rows", quality_report["duplicate_rows"])
        with qual_col3:
            st.metric("Total Cells", f"{quality_report['total_cells']:,}")

        with st.expander("Detailed Column Report"):
            for col_name, info in quality_report["columns"].items():
                st.markdown(f"**{col_name}** (`{info['dtype']}`)")
                st.markdown(
                    f"  - Non-null: {info['non_null_count']} | "
                    f"Null: {info['null_count']} ({info['null_percentage']}%) | "
                    f"Unique: {info['unique_count']} ({info['unique_percentage']}%)"
                )

    # Cross-module navigation
    st.markdown("---")
    st.markdown("### \U0001F517 Continue Analysis")
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    with nav_col1:
        st.page_link("pages/3_Data_Cleaning.py", label="\U0001f9f9 Clean This Data", icon="\U0001f9f9")
    with nav_col2:
        st.page_link("pages/4_AI_Insights_Engine.py", label="\U0001F916 AI Insights", icon="\U0001F916")
    with nav_col3:
        st.page_link("pages/8_Chat_With_Data.py", label="\U0001F4AC Chat With Data", icon="\U0001F4AC")
    with nav_col4:
        st.page_link("pages/7_Report_Generator.py", label="\U0001F4CB Generate Report", icon="\U0001F4CB")

else:
    st.info("Upload a file, paste data, or load a sample dataset to begin analysis.")

    # Show sample analysis with built-in data
    if "df" in st.session_state:
        st.markdown("---")
        st.markdown("### Preview with Built-in Data")
        st.markdown("While no file is uploaded, here is a preview using the built-in community college dataset.")
        st.dataframe(st.session_state.df.head(5), use_container_width=True)

