"""Data Cleaning Engine - Interactive data cleaning with undo/redo support."""
import streamlit as st
st.set_page_config(page_title="Data Cleaning", page_icon="\U0001f4a0", layout="wide")
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
    add_calculated_column,
    build_arithmetic_expression,
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

source_tab1, source_tab2 = st.tabs(["📁 Upload New File", "📂 Use Existing Data"])

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
                new_df = pd.read_csv(cleaning_upload)
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
                st.success(f"✅ Loaded **{cleaning_upload.name}** ({len(new_df):,} rows x {len(new_df.columns)} columns)")
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
            st.success(f"✅ Loaded '{selected_source}' for cleaning.")
            st.rerun()

# Check if working_df is loaded
if st.session_state.working_df is None:
    st.info("👆 Select a data source above to begin cleaning.")
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
tab_missing, tab_duplicates, tab_outliers, tab_columns, tab_calc, tab_validate = st.tabs(
    [
        "\U0001F50D Missing Values",
        "\U0001F503 Duplicates",
        "\U0001F4CA Outliers",
        "\U0001F527 Column Operations",
        "\U0001F9EE Calculated Columns",
        "\u2705 Validation Rules",
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
        "Engineer new features from existing columns using arithmetic. "
        "Build a formula with the guided builder, or write a custom expression."
    )

    numeric_cols_calc = df.select_dtypes(include=[np.number]).columns.tolist()

    calc_mode = st.radio(
        "Builder mode:",
        ["Guided builder", "Custom expression"],
        horizontal=True,
        key="calc_mode_radio",
    )

    new_col_name = st.text_input(
        "New column name:",
        key="calc_new_col_name",
        placeholder="e.g. Cost_Per_Credit",
    )

    if calc_mode == "Guided builder":
        if len(numeric_cols_calc) < 1:
            st.info("No numeric columns available to build a calculated column.")
        else:
            gb1, gb2, gb3, gb4 = st.columns([3, 1, 2, 3])
            with gb1:
                left_col = st.selectbox("Column", numeric_cols_calc, key="calc_left_col")
            with gb2:
                operator = st.selectbox("Op", ["+", "-", "*", "/"], key="calc_operator")
            with gb3:
                right_kind = st.radio(
                    "Operand", ["Column", "Value"], key="calc_right_kind", horizontal=False
                )
            with gb4:
                if right_kind == "Column":
                    right_operand = st.selectbox("With column", numeric_cols_calc, key="calc_right_col")
                    right_is_column = True
                else:
                    right_operand = st.number_input("With value", value=1.0, key="calc_right_val")
                    right_is_column = False

            expression_preview = build_arithmetic_expression(
                left_col, operator, right_operand, right_is_column=right_is_column
            )
            st.caption(f"Formula: `{new_col_name or 'new_column'} = {expression_preview}`")

            if st.button("Add Calculated Column", type="primary", key="calc_add_guided"):
                if not new_col_name.strip():
                    st.error("Please enter a name for the new column.")
                else:
                    try:
                        df.eval(expression_preview, engine="python")  # validate first
                        rows_affected = apply_cleaning_step(
                            f"Add calculated column '{new_col_name}' = {expression_preview}",
                            add_calculated_column,
                            new_col_name.strip(),
                            expression_preview,
                        )
                        save_session_state()
                        st.success(f"Created column '{new_col_name}' ({rows_affected:,} values).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not create column: {e}")

    else:  # Custom expression
        st.markdown(
            "Reference existing columns by name. Wrap names with spaces in "
            "backticks, e.g. `` `Course Cost` * 1.1 ``. Supported operators: "
            "`+ - * / // % **` and comparisons."
        )
        custom_expr = st.text_input(
            "Expression:",
            key="calc_custom_expr",
            placeholder="e.g. `Course_Cost` / `Credits`",
        )
        if custom_expr:
            st.caption(f"Formula: `{new_col_name or 'new_column'} = {custom_expr}`")
        if st.button("Add Calculated Column", type="primary", key="calc_add_custom"):
            if not new_col_name.strip():
                st.error("Please enter a name for the new column.")
            elif not custom_expr.strip():
                st.error("Please enter an expression.")
            else:
                try:
                    df.eval(custom_expr, engine="python")  # validate first
                    rows_affected = apply_cleaning_step(
                        f"Add calculated column '{new_col_name}' = {custom_expr}",
                        add_calculated_column,
                        new_col_name.strip(),
                        custom_expr.strip(),
                    )
                    save_session_state()
                    st.success(f"Created column '{new_col_name}' ({rows_affected:,} values).")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not evaluate expression: {e}")

# --- Validation Rules Tab ---
with tab_validate:
    st.markdown("#### Data Validation Rules")
    st.markdown(
        "Define expectations your data should meet, then run them to get a "
        "pass/fail report and inspect any violating rows."
    )

    vb1, vb2 = st.columns(2)
    with vb1:
        v_column = st.selectbox("Column", df.columns.tolist(), key="val_column")
    with vb2:
        v_rule_type = st.selectbox(
            "Rule type",
            list(RULE_TYPES.keys()),
            format_func=lambda k: RULE_TYPES[k],
            key="val_rule_type",
        )

    params = {}
    if v_rule_type == "range":
        rc1, rc2 = st.columns(2)
        with rc1:
            min_raw = st.text_input("Minimum (optional)", key="val_min")
        with rc2:
            max_raw = st.text_input("Maximum (optional)", key="val_max")
        if min_raw.strip():
            params["min"] = min_raw.strip()
        if max_raw.strip():
            params["max"] = max_raw.strip()
    elif v_rule_type == "allowed_values":
        allowed_raw = st.text_input(
            "Allowed values (comma-separated)", key="val_allowed",
            placeholder="e.g. Active, Inactive, Pending",
        )
        if allowed_raw.strip():
            params["allowed"] = [v.strip() for v in allowed_raw.split(",") if v.strip()]
    elif v_rule_type == "regex":
        params["pattern"] = st.text_input(
            "Regex pattern", key="val_pattern", placeholder=r"e.g. ^\d{4}-\d{2}-\d{2}$"
        )

    if st.button("Add Rule", key="val_add_rule"):
        new_rule = {"column": v_column, "rule_type": v_rule_type, "params": params}
        st.session_state.validation_rules.append(new_rule)
        st.success(f"Added rule: {describe_rule(new_rule)}")
        st.rerun()

    st.markdown("---")
    if st.session_state.validation_rules:
        st.markdown("##### Active Rules")
        for idx, rule in enumerate(st.session_state.validation_rules):
            rcol1, rcol2 = st.columns([8, 1])
            with rcol1:
                st.markdown(f"{idx + 1}. {describe_rule(rule)}")
            with rcol2:
                if st.button("\U0001F5D1\uFE0F", key=f"val_del_{idx}", help="Remove rule"):
                    st.session_state.validation_rules.pop(idx)
                    st.rerun()

        run_col, clear_col = st.columns([1, 1])
        with run_col:
            run_now = st.button("Run Validation", type="primary", key="val_run")
        with clear_col:
            if st.button("Clear All Rules", key="val_clear"):
                st.session_state.validation_rules = []
                st.rerun()

        # Optional: persist this rule set to the cloud
        if is_configured():
            rs_name = st.text_input(
                "Save rule set as", key="val_cloud_rs_name",
                placeholder="e.g. Enrollment expectations",
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
else:
    st.caption(
        "\u2601\uFE0F Tip: connect a database (see SUPABASE_SETUP.md) to save cleaned datasets to the cloud."
    )

# Cross-module navigation
st.markdown("---")
st.markdown("### \U0001F517 Next Steps")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/4_AI_Insights_Engine.py", label="\U0001F916 Analyze with AI", icon="\U0001F916")
with col2:
    st.page_link("pages/8_Chat_With_Data.py", label="\U0001F4AC Chat With Data", icon="\U0001F4AC")
with col3:
    st.page_link("pages/7_Report_Generator.py", label="\U0001F4CB Generate Report", icon="\U0001F4CB")
