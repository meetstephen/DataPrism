"""
Upload and Analyze - Universal dataset analysis tool.
"""

import streamlit as st
st.set_page_config(page_title="Upload & Analyze", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
import numpy as np
from utils.visualizations import (
    create_histogram,
    create_bar_chart,
    create_heatmap,
    create_box_plot
)
from utils.ai_insights import generate_data_quality_report
from utils.data_loader import SAMPLE_DATASETS, load_sample_dataset, parse_pasted_csv, load_file_flexible

st.title("\U0001F4C1 Upload & Analyze Your Data")
st.markdown(
    "Upload a CSV or Excel file — **including Power BI exported data (CSV/Excel)** — to get "
    "instant automated analysis, visualizations, and data-quality insights."
)

# --- Data Ingestion Tabs ---
ingest_tab_upload, ingest_tab_paste, ingest_tab_sample = st.tabs(
    ["\U0001F4C2 Upload File", "\U0001F4CB Paste Data", "\U0001F4E6 Sample Datasets"]
)

df = None  # Will hold the loaded dataframe

with ingest_tab_upload:
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls", "json", "tsv"],
        help="Upload CSV, Excel, JSON, or TSV files for analysis. Power BI: export as CSV or Excel."
    )

    if uploaded_file is not None:
        MAX_FILE_SIZE_MB = 50
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"File size ({file_size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit. "
                "Please upload a smaller file."
            )
        else:
            try:
                loaded_df, load_err = load_file_flexible(uploaded_file)
                if load_err:
                    st.error(load_err)
                elif loaded_df is not None:
                    df = loaded_df
                    st.session_state.uploaded_df = df
                    from utils.persistence import save_session_state
                    save_session_state()
                    st.success(f"File loaded successfully: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")

with ingest_tab_paste:
    st.markdown("Paste raw CSV, TSV, or delimited text below:")
    pasted_text = st.text_area(
        "Paste your data here",
        height=200,
        key="paste_data_area",
        placeholder="col1,col2,col3\nval1,val2,val3\n..."
    )
    if st.button("Load Pasted Data", type="primary", key="load_pasted_btn"):
        if pasted_text.strip():
            parsed_df, parse_err = parse_pasted_csv(pasted_text)
            if parse_err:
                st.error(parse_err)
            elif parsed_df is not None:
                df = parsed_df
                st.session_state.uploaded_df = df
                from utils.persistence import save_session_state
                save_session_state()
                st.success(f"Pasted data loaded: {len(df):,} rows x {len(df.columns)} columns")
        else:
            st.warning("Please paste some data first.")

with ingest_tab_sample:
    st.markdown("Load a built-in sample dataset to explore features:")
    for ds_name, ds_info in SAMPLE_DATASETS.items():
        with st.container():
            col_desc, col_btn = st.columns([3, 1])
            with col_desc:
                st.markdown(f"**{ds_info['name']}**")
                st.caption(ds_info["description"])
            with col_btn:
                if st.button("Load", key=f"load_sample_{ds_name}", use_container_width=True):
                    sample_df = load_sample_dataset(ds_name)
                    if sample_df is not None:
                        df = sample_df
                        st.session_state.uploaded_df = df
                        from utils.persistence import save_session_state
                        save_session_state()
                        st.success(f"Loaded '{ds_name}' ({len(df):,} rows)")

# Use session state uploaded_df if df was not set above (page reload)
if df is None and st.session_state.get("uploaded_df") is not None:
    df = st.session_state.uploaded_df

if df is not None:
    # Edge case: empty dataframe
    if len(df) == 0:
        st.warning("The dataset contains 0 rows. Please load a file with data.")
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

    # Download button for loaded data
    st.download_button(
        "\U0001F4E5 Download Data as CSV",
        df.to_csv(index=False),
        "analyzed_data.csv",
        "text/csv"
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
    missing_df_report = pd.DataFrame({
        "Column": missing.index,
        "Missing Count": missing.values,
        "Missing Percentage": (missing.values / len(df) * 100).round(2)
    })
    missing_df_report = missing_df_report[missing_df_report["Missing Count"] > 0]

    if len(missing_df_report) > 0:
        st.dataframe(missing_df_report, use_container_width=True)
        fig = create_bar_chart(
            missing_df_report, "Column", "Missing Percentage",
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

    # Cleaned Data Export
    st.markdown("---")
    st.markdown("### \U0001F4E5 Export Current Data")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "\U0001F4BE Download as CSV",
            df.to_csv(index=False),
            "export_data.csv",
            "text/csv",
            use_container_width=True,
        )
    with export_col2:
        from io import BytesIO
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button(
            "\U0001F4BE Download as Excel",
            excel_buffer.getvalue(),
            "export_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
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
