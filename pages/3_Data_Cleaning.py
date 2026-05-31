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
    flag_missing,
    cap_outliers,
    split_column,
    merge_columns,
    standardize_text,
    convert_column_type,
)
from utils.persistence import save_session_state
from utils.ai_client import generate_content, get_api_key

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
tab_missing, tab_duplicates, tab_outliers, tab_columns, tab_ai_clean, tab_text_type = st.tabs(
    ["\U0001F50D Missing Values", "\U0001F503 Duplicates", "\U0001F4CA Outliers", "\U0001F527 Column Operations", "\U0001F916 AI Cleaning Assistant", "\U0001F524 Text & Type Ops"]
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

        st.markdown("#### Flag Missing Values")
        st.caption("Create a boolean indicator column instead of dropping or filling missing values.")
        flag_col = st.selectbox(
            "Select column to flag missing values:",
            missing_cols.index.tolist(),
            key="flag_missing_col_select"
        )
        if flag_col and st.button("Flag Missing", type="primary", key="flag_missing_btn"):
            rows_affected = apply_cleaning_step(
                f"Flag missing in '{flag_col}' (new column: {flag_col}_is_missing)",
                flag_missing,
                flag_col
            )
            save_session_state()
            st.success(f"Flagged {rows_affected} missing values in '{flag_col}'. New indicator column added.")
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

                outlier_action_col1, outlier_action_col2 = st.columns(2)
                with outlier_action_col1:
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
                with outlier_action_col2:
                    if st.button("Cap Outliers", type="primary", key="cap_outliers_btn"):
                        rows_affected = apply_cleaning_step(
                            f"Cap outliers in '{outlier_col}' (IQR x{multiplier})",
                            cap_outliers,
                            outlier_col,
                            multiplier
                        )
                        save_session_state()
                        st.success(f"Capped {rows_affected} outlier values in '{outlier_col}' to IQR bounds.")
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

# --- AI Cleaning Assistant Tab ---
with tab_ai_clean:
    st.markdown("#### AI Cleaning Assistant")
    st.markdown("Describe what you want to do in plain English and let AI suggest the cleaning action.")

    api_key = get_api_key()
    if not api_key:
        st.info("Enter a Gemini API key in the sidebar or secrets to use the AI Cleaning Assistant.")
    else:
        ai_request = st.text_area(
            "Describe the cleaning operation you want:",
            placeholder="e.g., 'Remove all rows where Revenue is negative' or 'Convert the Date column to datetime format'",
            key="ai_clean_request",
            height=100,
        )

        if st.button("Ask AI", type="primary", key="ask_ai_clean_btn"):
            if not ai_request.strip():
                st.warning("Please describe what you want to do.")
            else:
                with st.spinner("AI is analyzing your request..."):
                    # Build schema context
                    schema_info = []
                    for col in df.columns:
                        dtype = str(df[col].dtype)
                        sample_vals = df[col].dropna().head(3).tolist()
                        schema_info.append(f"- {col} ({dtype}): sample values = {sample_vals}")
                    schema_text = "\n".join(schema_info)

                    prompt = f"""You are a data cleaning expert. The user has a DataFrame with these columns:
{schema_text}

The user wants: "{ai_request}"

Respond with EXACTLY this JSON format (no markdown, no code blocks):
{{"action": "brief description of cleaning action", "code": "single line of pandas code using variable 'df'", "preview": "what will change in plain English"}}

The code should be a single expression that transforms df and returns the new df (e.g., df.dropna(subset=['col']), df[df['col'] > 0], etc.).
Only use pandas operations. Never use exec, eval, import, or os."""

                    system = "You are a data cleaning assistant. Return only valid JSON."
                    try:
                        response_text, err = generate_content(prompt, api_key=api_key, system_instruction=system)
                        if err:
                            st.error(f"AI error: {err}")
                        elif response_text:
                            # Try to parse JSON from response
                            import json
                            try:
                                # Clean markdown code blocks if present
                                clean_text = response_text.strip()
                                if clean_text.startswith("```"):
                                    clean_text = clean_text.split("\n", 1)[1]
                                    clean_text = clean_text.rsplit("```", 1)[0]
                                ai_suggestion = json.loads(clean_text)
                                st.session_state["_ai_clean_suggestion"] = ai_suggestion
                            except (json.JSONDecodeError, IndexError):
                                st.info(f"AI suggestion: {response_text}")
                                st.session_state["_ai_clean_suggestion"] = {
                                    "action": "AI suggestion",
                                    "code": "",
                                    "preview": response_text,
                                }
                    except Exception as e:
                        st.error(f"AI request failed: {str(e)}")

        # Display suggestion and confirm button
        if "_ai_clean_suggestion" in st.session_state and st.session_state["_ai_clean_suggestion"]:
            suggestion = st.session_state["_ai_clean_suggestion"]
            st.markdown("---")
            st.markdown("**AI Suggested Action:**")
            st.info(suggestion.get("action", ""))
            if suggestion.get("preview"):
                st.markdown(f"**Preview:** {suggestion['preview']}")
            if suggestion.get("code"):
                st.code(suggestion["code"], language="python")

                if st.button("Confirm & Apply", type="primary", key="confirm_ai_clean_btn"):
                    try:
                        code = suggestion["code"]
                        # Safety check: block dangerous operations
                        blocked = ["import ", "exec(", "eval(", "os.", "sys.", "__", "open(", "subprocess"]
                        if any(b in code for b in blocked):
                            st.error("The suggested code contains unsafe operations and cannot be applied.")
                        else:
                            # Apply the operation
                            local_df = df.copy()
                            result_df = eval(code, {"__builtins__": {}}, {"df": local_df, "pd": pd, "np": np})
                            if isinstance(result_df, pd.DataFrame):
                                rows_diff = len(df) - len(result_df)
                                st.session_state.cleaning_history.append(st.session_state.working_df.copy())
                                st.session_state.working_df = result_df
                                from datetime import datetime
                                st.session_state.cleaning_log.append({
                                    "step": len(st.session_state.cleaning_log) + 1,
                                    "action": f"AI-assisted: {suggestion.get('action', 'custom operation')}",
                                    "rows_affected": abs(rows_diff),
                                    "timestamp": datetime.utcnow().isoformat(),
                                })
                                save_session_state()
                                st.session_state["_ai_clean_suggestion"] = None
                                st.success(f"Applied AI cleaning action. Rows affected: {abs(rows_diff)}")
                                st.rerun()
                            else:
                                st.error("The AI code did not return a valid DataFrame. Please try a different request.")
                    except Exception as e:
                        st.error(f"Failed to apply AI suggestion: {str(e)}")

# --- Text & Type Operations Tab ---
with tab_text_type:
    st.markdown("#### Text & Type Operations")

    text_ops_section, type_ops_section = st.columns(2)

    with text_ops_section:
        st.markdown("##### Text Standardization")
        text_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not text_cols:
            st.info("No text columns available for standardization.")
        else:
            std_col = st.selectbox(
                "Select text column:",
                text_cols,
                key="std_text_col_select"
            )
            std_mode = st.selectbox(
                "Standardization mode:",
                ["lowercase", "uppercase", "title", "strip"],
                key="std_mode_select"
            )
            if st.button("Apply Standardization", type="primary", key="apply_std_btn"):
                rows_affected = apply_cleaning_step(
                    f"Standardize text in '{std_col}' ({std_mode})",
                    standardize_text,
                    std_col,
                    std_mode
                )
                save_session_state()
                st.success(f"Applied {std_mode} to '{std_col}' ({rows_affected} values affected).")
                st.rerun()

    with type_ops_section:
        st.markdown("##### Type Conversion")
        type_col = st.selectbox(
            "Select column to convert:",
            df.columns.tolist(),
            key="type_conv_col_select"
        )
        target_type = st.selectbox(
            "Target type:",
            ["numeric", "datetime", "string", "category"],
            key="target_type_select"
        )
        if st.button("Convert Type", type="primary", key="apply_type_conv_btn"):
            rows_affected = apply_cleaning_step(
                f"Convert '{type_col}' to {target_type}",
                convert_column_type,
                type_col,
                target_type
            )
            save_session_state()
            st.success(f"Converted '{type_col}' to {target_type} ({rows_affected} values processed).")
            st.rerun()

    st.markdown("---")

    # Split Column
    st.markdown("##### Split Column")
    split_col_options = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if not split_col_options:
        st.info("No text columns available for splitting.")
    else:
        split_col_name = st.selectbox(
            "Select column to split:",
            split_col_options,
            key="split_col_select"
        )
        split_delimiter = st.text_input(
            "Delimiter:",
            value=",",
            key="split_delimiter_input",
            help="Character(s) to split on (e.g., comma, space, hyphen)"
        )
        split_new_names = st.text_input(
            "New column names (comma-separated):",
            placeholder="e.g., first_part, second_part",
            key="split_new_names_input"
        )
        if st.button("Split Column", type="primary", key="apply_split_btn"):
            if not split_delimiter:
                st.warning("Please provide a delimiter.")
            elif not split_new_names.strip():
                st.warning("Please provide new column names.")
            else:
                new_names = [n.strip() for n in split_new_names.split(",") if n.strip()]
                apply_cleaning_step(
                    f"Split '{split_col_name}' by '{split_delimiter}' into {new_names}",
                    split_column,
                    split_col_name,
                    split_delimiter,
                    new_names
                )
                save_session_state()
                st.success(f"Split '{split_col_name}' into {len(new_names)} new columns.")
                st.rerun()

    st.markdown("---")

    # Merge Columns
    st.markdown("##### Merge Columns")
    merge_col_options = df.columns.tolist()
    merge_cols_selected = st.multiselect(
        "Select columns to merge:",
        merge_col_options,
        key="merge_cols_select"
    )
    merge_separator = st.text_input(
        "Separator:",
        value=" ",
        key="merge_separator_input"
    )
    merge_new_name = st.text_input(
        "New column name:",
        placeholder="e.g., full_address",
        key="merge_new_name_input"
    )
    if len(merge_cols_selected) >= 2 and merge_new_name.strip():
        if st.button("Merge Columns", type="primary", key="apply_merge_btn"):
            apply_cleaning_step(
                f"Merge {merge_cols_selected} with '{merge_separator}' into '{merge_new_name}'",
                merge_columns,
                merge_cols_selected,
                merge_separator,
                merge_new_name.strip()
            )
            save_session_state()
            st.success(f"Merged {len(merge_cols_selected)} columns into '{merge_new_name}'.")
            st.rerun()
    elif merge_cols_selected and len(merge_cols_selected) < 2:
        st.caption("Select at least 2 columns to merge.")

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
    st.page_link("pages/8_Chat_With_Data.py", label="\U0001F4AC Chat With Data", icon="\U0001F4AC")
with col3:
    st.page_link("pages/7_Report_Generator.py", label="\U0001F4CB Generate Report", icon="\U0001F4CB")
