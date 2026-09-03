"""Data Cleaning Engine - Interactive data cleaning with undo/redo support."""
import streamlit as st
st.set_page_config(page_title="Data Cleaning", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_sidebar_nav
inject_global_css()
render_sidebar_nav()

import pandas as pd
import numpy as np
from utils.data_loader import read_csv_robust
from utils.data_engine import (
    init_cleaning_state,
    apply_cleaning_step,
    drop_missing_rows,
    fill_missing,
    remove_duplicates,
    remove_outliers_iqr,
    drop_columns,
    rename_columns,
    add_calculated_column,
    validate_calculated_expression,
    build_arithmetic_expression,
    flag_missing,
    cap_outliers,
    split_column,
    merge_columns,
    standardize_text,
    convert_column_type,
)
from utils.validation import run_validation, get_violation_mask, RULE_TYPES, describe_rule
from utils.exporters import render_export_buttons
from utils.supabase_client import is_configured
from utils import database as db
from utils.persistence import save_session_state

# Validation rules persist for the session
if "validation_rules" not in st.session_state:
    st.session_state.validation_rules = []

# Ensure cleaning state is initialized
init_cleaning_state()

st.title("\U0001f9f9 Data Cleaning Engine")
st.markdown("Clean, transform, and prepare your data with full undo support and audit logging.")

st.markdown("---")

# --- Data Source Selection ---
st.markdown("### Load Data")

source_tab1, source_tab2 = st.tabs(["ğŸ“ Upload New File", "ğŸ“‚ Use Existing Data"])

with source_tab1:
    cleaning_upload = st.file_uploader(
        "Upload a CSV or Excel file to clean",
        type=["csv", "xlsx", "xls"],
        key="cleaning_file_uploader",
        help="Upload a fresh dataset directly here for cleaning."
    )
    if cleaning_upload is not None:
        try:
            if cleaning_upload.name.endswith(".csv"):
                new_df, load_err = read_csv_robust(cleaning_upload)
                if load_err:
                    raise ValueError(load_err)
            else:
                new_df = pd.read_excel(cleaning_upload)
            if new_df.empty or len(new_df.columns) < 1:
                st.error("The uploaded file is empty or has no columns.")
            else:
                st.session_state.uploaded_df = new_df
                st.session_state.raw_df = new_df.copy()
                st.session_state.working_df = new_df.copy()
                st.session_state.cleaning_log = []
                st.session_state.cleaning_history = []
                st.session_state["_cleaning_source"] = "Uploaded Data"
                save_session_state()
                st.success(f"âœ… Loaded **{cleaning_upload.name}** ({len(new_df):,} rows x {len(new_df.columns)} columns)")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

with source_tab2:
    source_options = []
    if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
        source_options.append("Uploaded Data")
    if "online_df" in st.session_state and st.session_state.online_df is not None:
        source_options.append("Online Data")
    if "df" in st.session_state and st.session_state.df is not None:
        source_options.append("Built-in Dataset")

    if not source_options:
        st.info("No existing data loaded. Upload a file above, or load data from the Online Explorer or Home page.")
    else:
        selected_source = st.selectbox("Choose dataset to clean:", source_options)

        if st.button("Load Selected Dataset", type="primary", key="load_existing_for_cleaning"):
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
            save_session_state()
            st.success(f"âœ… Loaded '{selected_source}' for cleaning.")
            st.rerun()

# Check if working_df is loaded
if st.session_state.working_df is None:
    st.info("\U0001F446 Select a data source above to begin cleaning.")
    st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Or go to Upload & Analyze to load a file", icon="\U0001F4C1")
    st.stop()

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
tab_missing, tab_duplicates, tab_outliers, tab_columns, tab_calc, tab_validate, tab_ai_clean, tab_text_ops, tab_transforms = st.tabs(
    [
        "\U0001F50D Missing Values",
        "\U0001F503 Duplicates",
        "\U0001F4CA Outliers",
        "\U0001F527 Column Operations",
        "\U0001F9EE Calculated Columns",
        "\u2705 Validation Rules",
        "\U0001F916 AI Cleaning Assistant",
        "\U0001F524 Text & Type Operations",
        "\U0001F504 Column Transforms",
    ]
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
            save_session_state()
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
            save_session_state()
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
            save_session_state()
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
                    save_session_state()
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
        save_session_state()
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
            save_session_state()
            st.success(f"Renamed '{col_to_rename}' to '{new_name}'.")
            st.rerun()

# --- Calculated Columns Tab ---
with tab_calc:
    st.markdown("#### Create a Calculated Column")
    st.markdown(
        "Engineer new features from pectations",
            )
            if st.button("\u2601\uFE0F Save rules to cloud", key="val_cloud_save"):
                if not rs_name.strip():
                    st.error("Please enter a name for the rule set.")
                else:
                    ok, msg = db.save_rule_set(rs_name.strip(), st.session_state.validation_rules)
                    st.success(msg) if ok else st.error(msg)
        else:
            st.caption(
                "\u2601\uFE0F Tip: connect a database (see SUPABASE_SETUP.md) to save rule sets to the cloud."
            )

        if run_now:
            report = run_validation(df, st.session_state.validation_rules)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Rules Checked", report["total_rules"])
            with m2:
                st.metric("Passed", report["passed"])
            with m3:
                st.metric("Failed", report["failed"])

            results_df = pd.DataFrame(report["results"])[
                ["rule", "status", "violations", "violation_pct"]
            ].rename(columns={
                "rule": "Rule",
                "status": "Status",
                "violations": "Violations",
                "violation_pct": "% of Rows",
            })
            st.dataframe(results_df, use_container_width=True)

            failed_rules = [r for r in st.session_state.validation_rules
                            if run_validation(df, [r])["failed"] > 0]
            if failed_rules:
                st.markdown("##### Inspect Violating Rows")
                for idx, rule in enumerate(failed_rules):
                    with st.expander(f"\u26A0\uFE0F {describe_rule(rule)}"):
                        mask = get_violation_mask(df, rule)
                        st.dataframe(df[mask].head(50), use_container_width=True)
            else:
                st.success("All validation rules passed.")
    else:
        st.info("No rules defined yet. Add a rule above to start validating your data.")

# --- AI Cleaning Assistant Tab ---
with tab_ai_clean:
    st.markdown("#### AI Cleaning Assistant")
    st.markdown("Get AI-powered suggestions for cleaning your dataset.")

    from utils.ai_client import get_api_key, generate_content

    api_key = get_api_key()

    if st.button("Get AI Cleaning Suggestions", type="primary", key="ai_clean_suggest"):
        if not api_key:
            st.warning("Add a Gemini API key in the sidebar for AI suggestions.")
        else:
            with st.spinner("Analyzing dataset for cleaning suggestions..."):
                missing_info = df.isnull().sum().to_dict()
                dtypes_info = df.dtypes.astype(str).to_dict()
                prompt = (
                    "You are a data cleaning expert. Analyze this dataset and suggest "
                    "specific cleaning steps in priority order (most impactful first).\n\n"
                    f"Shape: {df.shape}\n"
                    f"Column types: {dtypes_info}\n"
                    f"Missing values: {missing_info}\n"
                    f"Duplicates: {int(df.duplicated().sum())}\n"
                    f"Sample:\n{df.head(3).to_string()}\n\n"
                    "Give 3-5 specific, actionable suggestions. Format as numbered list."
                )
                text, err = generate_content(prompt, api_key=api_key)
                if text:
                    st.markdown(text)
                else:
                    st.error(err or "Could not generate suggestions.")

    st.markdown("---")
    st.markdown("#### Quick Actions")

    qa_col1, qa_col2 = st.columns(2)
    with qa_col1:
        if st.button("\U0001F6A9 Flag All Missing Values", key="flag_all_missing"):
            missing_cols = [c for c in df.columns if df[c].isnull().any()]
            if missing_cols:
                rows_affected = apply_cleaning_step(
                    f"Flag missing in {len(missing_cols)} columns",
                    flag_missing, missing_cols
                )
                save_session_state()
                st.success(f"Flagged {rows_affected} missing values across {len(missing_cols)} columns.")
                st.rerun()
            else:
                st.info("No missing values to flag.")
    with qa_col2:
        cap_col_select = st.selectbox(
            "Cap outliers in:", df.select_dtypes(include=[np.number]).columns.tolist(),
            key="cap_outlier_col"
        )
        if st.button("\U0001F4CF Cap Outliers (Winsorize)", key="cap_outliers_btn"):
            if cap_col_select:
                rows_affected = apply_cleaning_step(
                    f"Cap outliers in '{cap_col_select}'",
                    cap_outliers, cap_col_select
                )
                save_session_state()
                st.success(f"Capped {rows_affected} outlier values in '{cap_col_select}'.")
                st.rerun()


# --- Text & Type Operations Tab ---
with tab_text_ops:
    st.markdown("#### Text Standardization")

    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    if not text_cols:
        st.info("No text columns available.")
    else:
        tt_col1, tt_col2 = st.columns(2)
        with tt_col1:
            text_col = st.selectbox("Text column:", text_cols, key="text_std_col")
        with tt_col2:
            text_method = st.selectbox(
                "Operation:", ["lowercase", "uppercase", "titlecase", "strip", "strip_all"],
                key="text_std_method"
            )
        if st.button("Apply Text Standardization", type="primary", key="apply_text_std"):
            rows_affected = apply_cleaning_step(
                f"Standardize '{text_col}' ({text_method})",
                standardize_text, text_col, text_method
            )
            save_session_state()
            st.success(f"Standardized {rows_affected} values in '{text_col}'.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### Type Conversion")
    all_cols = df.columns.tolist()
    tc_col1, tc_col2 = st.columns(2)
    with tc_col1:
        type_col = st.selectbox("Column:", all_cols, key="type_conv_col")
        if type_col:
            st.caption(f"Current type: {df[type_col].dtype}")
    with tc_col2:
        target_type = st.selectbox(
            "Convert to:", ["numeric", "text", "datetime", "integer", "float"],
            key="type_conv_target"
        )
    if st.button("Convert Type", type="primary", key="apply_type_conv"):
        rows_affected = apply_cleaning_step(
            f"Convert '{type_col}' to {target_type}",
            convert_column_type, type_col, target_type
        )
        save_session_state()
        st.success(f"Converted '{type_col}' to {target_type} ({rows_affected} values).")
        st.rerun()

    st.markdown("---")
    st.markdown("#### Split Column")
    if text_cols:
        sp_col1, sp_col2 = st.columns(2)
        with sp_col1:
            split_col_name = st.selectbox("Column to split:", text_cols, key="split_col_sel")
        with sp_col2:
            split_delim = st.text_input("Delimiter:", value=",", key="split_delim")
        if st.button("Split Column", type="primary", key="apply_split"):
            rows_affected = apply_cleaning_step(
                f"Split '{split_col_name}' by '{split_delim}'",
                split_column, split_col_name, split_delim
            )
            save_session_state()
            st.success(f"Split '{split_col_name}' ({rows_affected} rows processed).")
            st.rerun()

    st.markdown("---")
    st.markdown("#### Merge Columns")
    merge_cols_select = st.multiselect("Columns to merge:", all_cols, key="merge_cols_sel")
    merge_sep = st.text_input("Separator:", value=" ", key="merge_sep")
    merge_new_name = st.text_input("New column name:", key="merge_new_name", placeholder="e.g. full_address")
    if merge_cols_select and merge_new_name:
        if st.button("Merge Columns", type="primary", key="apply_merge"):
            rows_affected = apply_cleaning_step(
                f"Merge {merge_cols_select} into '{merge_new_name}'",
                merge_columns, merge_cols_select, merge_new_name.strip(), merge_sep
            )
            save_session_state()
            st.success(f"Merged {len(merge_cols_select)} columns into '{merge_new_name}'.")
            st.rerun()

# --- Column Transforms Tab ---
with tab_transforms:
    st.markdown("#### Column Transformations")
    st.markdown("Advanced column transformations to prepare data for modeling or analysis.")

    from utils.column_transforms import extract_date_parts, bin_numeric, one_hot_encode, string_operations

    transform_section = st.radio(
        "Transformation type:",
        ["Date Part Extraction", "Numeric Binning", "One-Hot Encoding", "String Regex Extract"],
        horizontal=True,
        key="transform_section_radio",
    )

    if transform_section == "Date Part Extraction":
        st.markdown("##### Extract Date Parts")
        st.markdown("Extract year, month, day, and weekday from a datetime column.")
        # Find datetime-like columns
        date_cols = df.select_dtypes(include=["datetime", "datetime64", "datetimetz"]).columns.tolist()
        # Also consider object columns that may contain dates
        for col in df.select_dtypes(include=["object"]).columns:
            try:
                sample = df[col].dropna().head(20)
                if len(sample) > 0:
                    parsed = pd.to_datetime(sample, errors="coerce")
                    if parsed.notna().sum() > len(sample) * 0.5:
                        date_cols.append(col)
            except Exception:
                pass

        if not date_cols:
            st.info("No datetime columns detected. Convert a column to datetime in the 'Text & Type Operations' tab first.")
        else:
            date_col = st.selectbox("Select datetime column:", date_cols, key="transform_date_col")
            if st.button("Extract Date Parts", type="primary", key="transform_extract_dates"):
                rows_affected = apply_cleaning_step(
                    f"Extract date parts from '{date_col}'",
                    extract_date_parts,
                    date_col,
                )
                save_session_state()
                st.success(f"Extracted year, month, day, weekday from '{date_col}' ({rows_affected:,} rows).")
                st.rerun()

    elif transform_section == "Numeric Binning":
        st.markdown("##### Bin Numeric Column")
        st.markdown("Create categorical bins from a numeric column.")
        numeric_cols_bin = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols_bin:
            st.info("No numeric columns available for binning.")
        else:
            bin_col = st.selectbox("Select numeric column:", numeric_cols_bin, key="transform_bin_col")
            n_bins = st.slider("Number of bins:", min_value=2, max_value=20, value=5, key="transform_n_bins")
            if bin_col:
                st.caption(f"Preview: will create '{bin_col}_binned' with {n_bins} equal-width intervals.")
            if st.button("Apply Binning", type="primary", key="transform_apply_bin"):
                rows_affected = apply_cleaning_step(
                    f"Bin '{bin_col}' into {n_bins} bins",
                    bin_numeric,
                    bin_col,
                    n_bins,
                )
                save_session_state()
                st.success(f"Created '{bin_col}_binned' column ({rows_affected:,} rows binned).")
                st.rerun()

    elif transform_section == "One-Hot Encoding":
        st.markdown("##### One-Hot Encode")
        st.markdown("Convert a categorical column into binary indicator columns.")
        cat_cols_ohe = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not cat_cols_ohe:
            st.info("No categorical columns available for encoding.")
        else:
            ohe_col = st.selectbox("Select categorical column:", cat_cols_ohe, key="transform_ohe_col")
            drop_original = st.checkbox("Drop original column after encoding", value=False, key="transform_ohe_drop")
            if ohe_col:
                unique_vals = df[ohe_col].nunique()
                st.caption(f"Will create {unique_vals} new binary columns (one per unique value).")
            if st.button("Apply One-Hot Encoding", type="primary", key="transform_apply_ohe"):
                rows_affected = apply_cleaning_step(
                    f"One-hot encode '{ohe_col}' (drop_original={drop_original})",
                    one_hot_encode,
                    ohe_col,
                    drop_original,
                )
                save_session_state()
                st.success(f"One-hot encoded '{ohe_col}' ({rows_affected:,} rows).")
                st.rerun()

    elif transform_section == "String Regex Extract":
        st.markdown("##### Regex Extract")
        st.markdown("Extract text matching a regex pattern into a new column.")
        text_cols_re = df.select_dtypes(include=["object"]).columns.tolist()
        if not text_cols_re:
            st.info("No text columns available for regex extraction.")
        else:
            re_col = st.selectbox("Select text column:", text_cols_re, key="transform_re_col")
            re_pattern = st.text_input(
                "Regex pattern:",
                key="transform_re_pattern",
                placeholder=r"e.g. \d{4}-\d{2}-\d{2} or [A-Z]+",
            )
            if re_col and re_pattern:
                st.caption(f"Matches will be saved to '{re_col}_extracted'.")
            if st.button("Apply Regex Extract", type="primary", key="transform_apply_regex"):
                if not re_pattern.strip():
                    st.error("Please enter a regex pattern.")
                else:
                    rows_affected = apply_cleaning_step(
                        f"Regex extract '{re_pattern}' from '{re_col}'",
                        string_operations,
                        re_col,
                        "extract_regex",
                        re_pattern.strip(),
                    )
                    save_session_state()
                    st.success(f"Extracted matches to '{re_col}_extracted' ({rows_affected:,} matches found).")
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
st.caption("Download your cleaned dataset in the format that fits your next tool.")
render_export_buttons(
    st.session_state.working_df,
    base_filename="cleaned_data",
    key_prefix="cleaning_export",
)

# Optional: save the cleaned dataset to the cloud
if is_configured():
    with st.expander("\u2601\uFE0F Save cleaned dataset to the cloud"):
        clean_name = st.text_input("Save as name", key="clean_cloud_name", placeholder="e.g. cleaned_enrollment")
        if st.button("Save to cloud", key="clean_cloud_save"):
            if not clean_name.strip():
                st.error("Please enter a name.")
            else:
                ok, msg = db.save_dataset(clean_name.strip(), st.session_state.working_df, "Cleaned in DataPrism")
                st.success(msg) if ok else st.error(msg)
                if ok:
                    try:
                        from utils.auth import log_user_activity
                        log_user_activity("cleaning_saveeÌµ±¥­”‘…Ñ…Í•Ğ¸ˆˆˆ(€€€¥µÁ½ÉĞ¹ÕµÁä…Ì¹À(€€€¹À¹É…¹‘½´¹Í•• ĞÈ¤(€€€ÍÁ•¥•Ì€ô¹À¹É•Á•…Ğ¡l‰Í•Ñ½Í„ˆ°€‰Ù•ÉÍ¥½±½Èˆ°€‰Ù¥É¥¹¥„‰t°€ÔÀ¤(€€€Í•Á…±}±•¹Ñ €ô¹À¹½¹…Ñ•¹…Ñ”¡l(€€€€€€€¹À¹É…¹‘½´¹¹½Éµ…±¹Ì€ô¹À¹É…¹‘½´¹¡½¥”¡l‰9½ÉÑ ˆ°€‰M½ÕÑ ˆ°€‰…ÍĞˆ°€‰]•ÍĞ‰t°¸¤(€€€ÁÉ½‘ÕÑÌ€ô¹À¹É…¹‘½´¹¡½¥”¡l‰]¥‘•Ğˆ°€‰]¥‘•Ğˆ°€‰…‘•Ğ`ˆ°€‰…‘•Ğdˆ°€‰AÉ•µ¥Õ´h‰t°¸¤(€€€‘…Ñ•Ì€ôÁ¹‘…Ñ•}É…¹” ˆÈÀÈÌ´Â" ¢FbÒFbæ6÷’‚¢–bÖWF†öBÓÒ&—"# ¢ÒFe¶6öÇVÖåÒçVçF–ÆRƒã#R¢2ÒFe¶6öÇVÖåÒçVçF–ÆRƒãsR¢•"Ò2Ò¢Æ÷vW"ÒÒ×VÇF—Æ–W"¢• ¢WW"Ò2²×VÇF—Æ–W"¢• ¢VÇ6S ¢2W&6VçF–ÆRÖWF†ö@¢Æ÷vW"ÒFe¶6öÇVÖåÒçVçF–ÆRƒã¢WW"ÒFe¶6öÇVÖåÒçVçF–ÆRƒã“’ ¢Ö6²Ò†Fe¶6öÇVÖåÒÂÆ÷vW"’Â†Fe¶6öÇVÖåÒâWW"¢&÷w5öffV7FVBÒ–çB†Ö6²ç7VÒ‚’¢Fe¶6öÇVÖåÒÒFe¶6öÇVÖåÒæ6Æ—†Æ÷vW#ÖÆ÷vW"ÂWW#×WW"¢&WGW&âFbÂ&÷w5öffV7FV@  ¦FVb7Æ—Eö6öÇVÖâ†FbÂ6öÇVÖâÂFVÆ–Ö—FW#Ò"Â"ÂæWuö6öÅöæÖW3ÔæöæR“ ¢""%7Æ—BFW‡B6öÇVÖâ–çFò×VÇF—ÆR6öÇVÖç2'’FVÆ–Ö—FW"à ¢&WGW&ç2†FbÂ&÷w5öffV7FVB’à¢"" ¢FbÒFbæ6÷’‚¢7Æ—E÷&W7VÇBÒFe¶6öÇVÖåÒæ7G—R‡7G"’ç7G"ç7Æ—B†FVÆ–Ö—FW"ÂW‡æCÕG'VR¢åöæWuö6öÇ2Ò7Æ—E÷&W7VÇBç6†U³Ğ ¢–bæWuö6öÅöæÖW2æBÆVâ†æWuö6öÅöæÖW2’ãÒåöæWuö6öÇ3 ¢æÖW2ÒæWuö6öÅöæÖW5³¦åöæWuö6öÇ5Ğ¢VÇ6S ¢æÖW2Ò¶b'¶6öÇVÖçÕ÷'G¶’³Ò"f÷"’–â&ævR†åöæWuö6öÇ2•Ğ ¢f÷"’ÂæÖR–âVçVÖW&FR†æÖW2“ ¢Fe¶æÖUÒÒ7Æ—E÷&W7VÇE¶•Òç7G"ç7G&—‚’–b7Æ—E÷&W7VÇE¶•Ò—2æ÷BæöæRVÇ6RæöæP ¢&÷w5öffV7FVBÒ–çB†Fe¶6öÇVÖåÒææ÷Fæ‚’ç7VÒ‚’¢&WGW&âFbÂ&÷w5öffV7FV@  ¦FVbÖW&vUö6öÇVÖç2†FbÂ6öÇVÖç2ÂæWuö6öÅöæÖRÂ6W&F÷#Ò""“ ¢""$ÖW&vR×VÇF—ÆR6öÇVÖç2–çFòöæR'’6öæ6FVæF–ærF†V—"7G&–ærfÇVW2à ¢&WGW&ç2†FbÂ&÷w5öffV7FVB’à¢"" ¢FbÒFbæ6÷’‚¢Fe¶æWuö6öÅöæÖUÒÒFe¶6öÇVÖç5Òæ7G—R‡7G"’ævr‡6W&F÷"æ¦ö–âÂ†—3Ó¢&÷w5öffV7FVBÒÆVâ†Fb¢&WGW&âFbÂ&÷w5öffV7FV@  ¦FVb7FæF&F—¦U÷FW‡B†FbÂ6öÇVÖâÂÖWF†öCÒ&Æ÷vW&66R"“ ¢""%7FæF&F—¦RFW‡B–â6öÇVÖâà ¢ÖWF†öG3¢Æ÷vW&66RÂWW&66RÂF—FÆV66RÂ7G&—Â7G&—öÆÂà¢&WGW&ç2†FbÂ&÷w5öffV7FVB’à¢"" ¢FbÒFbæ6÷’‚¢6W&–W2ÒFe¶6öÇVÖåĞ¢&÷w5öffV7FVBÒ–çB‡6W&–W2ææ÷Fæ‚’ç7VÒ‚’ ¢–bÖWF†öBÓÒ&Æ÷vW&66R# ¢Fe¶6öÇVÖåÒÒ6W&–W2æ7G—R‡7G"’ç7G"æÆ÷vW"‚¢VÆ–bÖWF†öBÓÒ'WW&66R# ¢Fe¶6öÇVÖåÒÒ6W&–W2æ7G—R‡7G"’ç7G"çWW"‚¢VÆ–bÖWF†öBÓÒ'F—FÆV66R# ¢Fe¶6öÇVÖåÒÒ6W&–W2æ7G—R‡7G"’ç7G"çF—FÆR‚¢VÆ–bÖWF†öBÓÒ'7G&—# ¢Fe¶6öÇVÖåÒÒ6W&–W2æ7G—R‡7G"’ç7G"ç7G&—‚¢VÆ–bÖWF†öBÓÒ'7G&—öÆÂ# ¢Fe¶6öÇVÖåÒÒ6W&–W2æ7G—R‡7G"’ç7G"ç&WÆ6R‡"%Ç2²"Â""Â&VvWƒÕG'VR’ç7G"ç7G&—‚ ¢&WGW&âFbÂ&÷w5öffV7FV@  ¦FVb6öçfW'Eö6öÇVÖå÷G—R†FbÂ6öÇVÖâÂF&vWE÷G—R“ ¢""$6öçfW'B6öÇVÖâFòF–ffW&VçBFFG—Rà ¢7W÷'FVBF&vWE÷G—S¢vçVÖW&–2rÂwFW‡BrÂvFFWF–ÖRrÂv–çFVvW"rÂvfÆöBrà¢&WGW&ç2†FbÂ&÷w5öffV7FVB’à¢"" ¢FbÒFbæ6÷’‚¢&÷w5öffV7FVBÒ–çB†Fe¶6öÇVÖåÒææ÷Fæ‚’ç7VÒ‚’ ¢–bF&vWE÷G—RÓÒ&çVÖW&–2# ¢Fe¶6öÇVÖåÒÒBçFõöçVÖW&–2†Fe¶6öÇVÖåÒÂW'&÷'3Ò&6öW&6R"¢VÆ–bF&vWE÷G—RÓÒ&–çFVvW"# ¢Fe¶6öÇVÖåÒÒBçFõöçVÖW&–2†Fe¶6öÇVÖåÒÂW'&÷'3Ò&6öW&6R"¢Fe¶6öÇVÖåÒÒFe¶6öÇVÖåÒæ7G—R‚$–çCcB"¢VÆ–bF&vWE÷G—RÓÒ&fÆöB# ¢Fe¶6öÇVÖåÒÒBçFõöçVÖW&–2†Fe¶6öÇVÖåÒÂW'&÷'3Ò&6öW&6R"’æ7G—R†fÆöB¢VÆ–bF&vWE÷G—RÓÒ'FW‡B# ¢Fe¶6öÇVÖåÒÒFe¶6öÇVÖåÒæ7G—R‡7G"¢VÆ–bF&vWE÷G—RÓÒ&FFWF–ÖR# ¢Fe¶6öÇVÖåÒÒBçFõöFFWF–ÖR†Fe¶6öÇVÖåÒÂW'&÷'3Ò&6öW&6R" ¢&WGW&âFbÂ&÷w5öffV7FV@ 