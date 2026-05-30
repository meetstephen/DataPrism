"""Data Cleaning Engine - Interactive data cleaning with undo/redo support."""
import streamlit as st
st.set_page_config(page_title="Data Cleaning", page_icon="\U0001f9f9", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
import numpy as np
from utils.data_engine import (
    init_cleaning_state,
    apply_cleaning_step,
    drop_missing_rows,
    fill_missing,
    remove_duplicates,
    remove_outliers_iqr,
    drop_columns,
    rename_columns,
)

# Ensure cleaning state is initialized
init_cleaning_state()

st.title("\U0001f9f9 Data Cleaning Engine")
st.markdown("Clean, transform, and prepare your data with full undo support and audit logging.")

st.markdown("---")

# --- Data Source Selection ---
st.markdown("### Select Data Source")
source_options = []
if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    source_options.append("Uploaded Data")
if "online_df" in st.session_state and st.session_state.online_df is not None:
    source_options.append("Online Data")
if "df" in st.session_state and st.session_state.df is not None:
    source_options.append("Built-in Dataset")

if not source_options:
    st.warning("No data available. Please upload a dataset or load the built-in data from the home page.")
    st.stop()

selected_source = st.selectbox("Choose dataset to clean:", source_options)

# Load data into working_df on first selection or source change
load_key = f"cleaning_source_{selected_source}"
if st.session_state.working_df is None or st.session_state.get("_cleaning_source") != selected_source:
    if selected_source == "Uploaded Data":
        st.session_state.raw_df = st.session_state.uploaded_df.copy()
    elif selected_source == "Online Data":
        st.session_state.raw_df = st.session_state.online_df.copy()
    else:
        st.session_state.raw_df = st.session_state.df.copy()
    st.session_state.working_df = st.session_state.raw_df.copy()
    st.session_state.cleaning_log = []
    st.session_state.cleaning_history = []
    st.session_state["_cleaning_source"] = selected_source

df = st.session_state.working_df

# --- Undo / Reset Toolbar ---
st.markdown("---")
tool_col1, tool_col2, tool_col3 = st.columns([1, 1, 4])
with tool_col1:
    if st.button("\u21A9\uFE0F Undo Last Step", use_container_width=True):
        if st.session_state.cleaning_history:
            st.session_state.working_df = st.session_state.cleaning_history.pop()
            if st.session_state.cleaning_log:
                st.session_state.cleaning_log.pop()
            st.rerun()
        else:
            st.toast("Nothing to undo.", icon="\u26a0\ufe0f")

with tool_col2:
    if st.button("\U0001F504 Reset to Original", use_container_width=True):
        st.session_state.working_df = st.session_state.raw_df.copy()
        st.session_state.cleaning_log = []
        st.session_state.cleaning_history = []
        st.rerun()

# --- Data Shape Metrics ---
st.markdown("### Current Data Overview")
met_col1, met_col2, met_col3, met_col4 = st.columns(4)
with met_col1:
    st.metric("Rows", f"{len(df):,}")
with met_col2:
    st.metric("Columns", f"{len(df.columns)}")
with met_col3:
    missing_total = int(df.isnull().sum().sum())
    st.metric("Missing Values", f"{missing_total:,}")
with met_col4:
    total_cells = len(df) * len(df.columns)
    completeness = ((total_cells - missing_total) / total_cells * 100) if total_cells > 0 else 100
    st.metric("Completeness", f"{completeness:.1f}%")

st.markdown("---")

# --- Cleaning Tabs ---
tab_missing, tab_duplicates, tab_outliers, tab_columns = st.tabs(
    ["\U0001F50D Missing Values", "\U0001F503 Duplicates", "\U0001F4CA Outliers", "\U0001F527 Column Operations"]
)

# --- Missing Values Tab ---
with tab_missing:
    st.markdown("#### Missing Value Analysis")

    missing_counts = df.isnull().sum()
    missing_cols = missing_counts[missing_counts > 0]

    if missing_cols.empty:
        st.success("No missing values detected in the dataset.")
    else:
        st.dataframe(
            pd.DataFrame({
                "Column": missing_cols.index,
                "Missing Count": missing_cols.values,
                "% Missing": (missing_cols.values / len(df) * 100).round(2)
            }).reset_index(drop=True),
            use_container_width=True
        )

        st.markdown("#### Fill Missing Values")
        fill_col = st.selectbox(
            "Select column to fill:",
            missing_cols.index.tolist(),
            key="fill_col_select"
        )

        is_numeric = pd.api.types.is_numeric_dtype(df[fill_col]) if fill_col else False
        if is_numeric:
            strategy_options = ["mean", "median", "mode", "zero", "forward", "backward"]
        else:
            strategy_options = ["mode", "forward", "backward"]

        fill_strategy = st.selectbox(
            "Fill strategy:",
            strategy_options,
            key="fill_strategy_select"
        )

        if st.button("Apply Fill", type="primary", key="apply_fill_btn"):
            rows_affected = apply_cleaning_step(
                f"Fill missing in '{fill_col}' with {fill_strategy}",
                fill_missing,
                fill_col,
                fill_strategy
            )
            st.success(f"Filled {rows_affected} missing values in '{fill_col}' using {fill_strategy}.")
            st.rerun()

        st.markdown("#### Drop Rows with Missing Values")
        drop_cols = st.multiselect(
            "Drop rows where these columns have missing values:",
            missing_cols.index.tolist(),
            key="drop_missing_cols"
        )
        if drop_cols and st.button("Drop Rows", type="primary", key="drop_rows_btn"):
            rows_affected = apply_cleaning_step(
                f"Drop rows missing in {drop_cols}",
                drop_missing_rows,
                drop_cols
            )
            st.success(f"Removed {rows_affected} rows with missing values.")
            st.rerun()

# --- Duplicates Tab ---
with tab_duplicates:
    st.markdown("#### Duplicate Row Detection")

    dup_count = int(df.duplicated().sum())
    st.metric("Duplicate Rows Found", f"{dup_count:,}")

    if dup_count > 0:
        with st.expander("Preview Duplicate Rows"):
            st.dataframe(df[df.duplicated(keep=False)].head(20), use_container_width=True)

        keep_strategy = st.selectbox(
            "Keep strategy:",
            ["first", "last", False],
            format_func=lambda x: "Keep First" if x == "first" else "Keep Last" if x == "last" else "Remove All Duplicates",
            key="dup_keep_strategy"
        )

        if st.button("Remove Duplicates", type="primary", key="remove_dups_btn"):
            rows_affected = apply_cleaning_step(
                f"Remove duplicates (keep={keep_strategy})",
                remove_duplicates,
                keep_strategy
            )
            st.success(f"Removed {rows_affected} duplicate rows.")
            st.rerun()
    else:
        st.success("No duplicate rows found in the dataset.")

# --- Outliers Tab ---
with tab_outliers:
    st.markdown("#### Outlier Detection (IQR Method)")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        st.info("No numeric columns available for outlier detection.")
    else:
        outlier_col = st.selectbox(
            "Select numeric column:",
            numeric_cols,
            key="outlier_col_select"
        )

        multiplier = st.slider(
            "IQR Multiplier:",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            key="iqr_multiplier",
            help="Lower values remove more outliers. Standard is 1.5."
        )

        if outlier_col:
            Q1 = df[outlier_col].quantile(0.25)
            Q3 = df[outlier_col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR
            outlier_mask = (df[outlier_col] < lower) | (df[outlier_col] > upper)
            outlier_count = int(outlier_mask.sum())

            bounds_col1, bounds_col2, bounds_col3 = st.columns(3)
            with bounds_col1:
                st.metric("Lower Bound", f"{lower:.2f}")
            with bounds_col2:
                st.metric("Upper Bound", f"{upper:.2f}")
            with bounds_col3:
                st.metric("Outliers Found", f"{outlier_count:,}")

            if outlier_count > 0:
                with st.expander("Preview Outlier Rows"):
                    st.dataframe(df[outlier_mask].head(20), use_container_width=True)

                if st.button("Remove Outliers", type="primary", key="remove_outliers_btn"):
                    rows_affected = apply_cleaning_step(
                        f"Remove outliers in '{outlier_col}' (IQR x{multiplier})",
                        remove_outliers_iqr,
                        outlier_col,
                        multiplier
                    )
                    st.success(f"Removed {rows_affected} outlier rows from '{outlier_col}'.")
                    st.rerun()
            else:
                st.success(f"No outliers detected in '{outlier_col}' with multiplier {multiplier}.")

# --- Column Operations Tab ---
with tab_columns:
    st.markdown("#### Drop Columns")
    cols_to_drop = st.multiselect(
        "Select columns to drop:",
        df.columns.tolist(),
        key="cols_to_drop_select"
    )
    if cols_to_drop and st.button("Drop Selected Columns", type="primary", key="drop_cols_btn"):
        apply_cleaning_step(
            f"Drop columns: {cols_to_drop}",
            drop_columns,
            cols_to_drop
        )
        st.success(f"Dropped {len(cols_to_drop)} column(s).")
        st.rerun()

    st.markdown("---")
    st.markdown("#### Rename Columns")
    col_to_rename = st.selectbox(
        "Select column to rename:",
        df.columns.tolist(),
        key="col_to_rename_select"
    )
    new_name = st.text_input(
        "New column name:",
        value=col_to_rename if col_to_rename else "",
        key="new_col_name_input"
    )
    if col_to_rename and new_name and new_name != col_to_rename:
        if st.button("Rename Column", type="primary", key="rename_col_btn"):
            apply_cleaning_step(
                f"Rename '{col_to_rename}' to '{new_name}'",
                rename_columns,
                {col_to_rename: new_name}
            )
            st.success(f"Renamed '{col_to_rename}' to '{new_name}'.")
            st.rerun()

# --- Cleaning Log ---
st.markdown("---")
st.markdown("### \U0001F4DC Cleaning Audit Log")
if st.session_state.cleaning_log:
    log_df = pd.DataFrame(st.session_state.cleaning_log)
    st.dataframe(log_df, use_container_width=True)
else:
    st.info("No cleaning operations performed yet. Use the tabs above to clean your data.")

# --- Download Cleaned Data ---
st.markdown("---")
st.markdown("### \U0001F4E5 Export Cleaned Data")
download_col1, download_col2 = st.columns([1, 3])
with download_col1:
    csv_data = st.session_state.working_df.to_csv(index=False)
    st.download_button(
        "\U0001F4BE Download Cleaned CSV",
        csv_data,
        file_name="cleaned_data.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )

# Cross-module navigation
st.markdown("---")
st.markdown("### \U0001F517 Next Steps")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/4_AI_Insights_Engine.py", label="\U0001F916 Analyze with AI", icon="\U0001F916")
with col2:
    st.page_link("pages/10_Chat_With_Data.py", label="\U0001F4AC Chat With Data", icon="\U0001F4AC")
with col3:
    st.page_link("pages/7_Report_Generator.py", label="\U0001F4CB Generate Report", icon="\U0001F4CB")
