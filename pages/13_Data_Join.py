"""
Data Join & Merge - Combine multiple datasets using joins or concatenation.
"""

import streamlit as st
st.set_page_config(page_title="Data Join & Merge", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_sidebar_nav
inject_global_css()
render_sidebar_nav()
from utils.data_loader import ensure_builtin_data
ensure_builtin_data()

import pandas as pd
from utils.data_join import get_available_datasets, join_datasets, concat_datasets

st.title("\U0001F517 Data Join & Merge")
st.markdown("Combine multiple datasets using joins, merges, or concatenation.")

with st.expander("❓ How to use this page", expanded=False):
    st.markdown("""
    1. You need **at least 2 datasets** loaded (upload multiple files, or load one from Online Explorer)
    2. **Join tab**: Pick left/right datasets, select key columns, choose join type (inner/left/right/outer)
    3. **Concatenate tab**: Stack datasets vertically (append rows) or horizontally (add columns)
    4. Preview the result, then **Save to Session** to use it on other pages
    """)

# --- Direct file upload option ---
with st.expander("\U0001F4C1 Upload your own file directly", expanded=False):
    join_file = st.file_uploader(
        "Upload CSV, Excel, JSON, TSV, or Parquet",
        type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
        key="join_file_upload",
        help="File will also be saved to your session for use on other pages.",
    )
    if join_file is not None:
        from utils.data_loader import load_file_flexible
        loaded, err = load_file_flexible(join_file)
        if err:
            st.error(err)
        elif loaded is not None:
            st.session_state.uploaded_df = loaded.copy()
            st.success(f"Loaded: {join_file.name} ({len(loaded):,} rows)")

st.markdown("---")

# Check available datasets
datasets = get_available_datasets()

if len(datasets) < 1:
    st.warning("No datasets available. Please load data first using the Upload & Analyze page or the file uploader above.")
    st.stop()

# --- Tabs for Join vs Concatenate ---
tab_join, tab_concat = st.tabs(["\U0001F517 Join / Merge", "\U0001F4DA Concatenate / Stack"])

# =================== JOIN TAB ===================
with tab_join:
    st.subheader("Join Two Datasets")
    st.markdown("Merge two datasets based on a common key column.")

    if len(datasets) < 2:
        st.info("You need at least **2 datasets** loaded to perform a join. Upload another file above or load data from other pages.")
    else:
        dataset_names = list(datasets.keys())

        col1, col2 = st.columns(2)
        with col1:
            left_name = st.selectbox("Left Dataset", dataset_names, key="join_left_ds")
        with col2:
            right_name = st.selectbox(
                "Right Dataset",
                [n for n in dataset_names if n != left_name] if len(dataset_names) > 1 else dataset_names,
                key="join_right_ds",
            )

        left_df = datasets[left_name]
        right_df = datasets[right_name]

        # Show dataset info
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"**{left_name}**: {len(left_df):,} rows, {len(left_df.columns)} columns")
        with col_info2:
            st.caption(f"**{right_name}**: {len(right_df):,} rows, {len(right_df.columns)} columns")

        # Join configuration
        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
        with col_cfg1:
            left_key = st.selectbox("Left Key Column", left_df.columns.tolist(), key="join_left_key")
        with col_cfg2:
            right_key = st.selectbox("Right Key Column", right_df.columns.tolist(), key="join_right_key")
        with col_cfg3:
            join_type = st.selectbox(
                "Join Type",
                ["inner", "left", "right", "outer"],
                help="inner: only matching rows | left: all left + matching right | right: all right + matching left | outer: all rows from both",
                key="join_type_select",
            )

        # Execute join
        if st.button("\U0001F517 Perform Join", type="primary", key="btn_join"):
            try:
                result = join_datasets(left_df, right_df, left_key, right_key, join_type)
                st.session_state["_join_preview"] = result
                st.success(f"Join complete! Result: {len(result):,} rows, {len(result.columns)} columns")
            except Exception as e:
                st.error(f"Join failed: {str(e)}")

        # Preview and save
        if "_join_preview" in st.session_state and st.session_state["_join_preview"] is not None:
            preview_df = st.session_state["_join_preview"]
            st.markdown("#### Preview (first 100 rows)")
            st.dataframe(preview_df.head(100), use_container_width=True)

            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.button("\U0001F4BE Save to Session", key="save_join_result"):
                    st.session_state.join_result_df = preview_df.copy()
                    st.session_state.merged_df = preview_df.copy()
                    st.success("Saved as 'Join Result' and 'Merged Data' - available across all pages!")

# =================== CONCATENATE TAB ===================
with tab_concat:
    st.subheader("Concatenate Datasets")
    st.markdown("Stack multiple datasets vertically (append rows) or horizontally (add columns).")

    if len(datasets) < 2:
        st.info("You need at least **2 datasets** loaded to concatenate. Upload another file above or load data from other pages.")
    else:
        dataset_names = list(datasets.keys())

        selected_datasets = st.multiselect(
            "Select datasets to concatenate",
            dataset_names,
            default=dataset_names[:2],
            key="concat_select",
        )

        concat_axis = st.radio(
            "Concatenation Direction",
            ["Vertical (stack rows)", "Horizontal (add columns)"],
            horizontal=True,
            key="concat_axis",
        )
        axis = 0 if "Vertical" in concat_axis else 1

        if selected_datasets:
            # Show selected dataset info
            for name in selected_datasets:
                df_info = datasets[name]
                st.caption(f"**{name}**: {len(df_info):,} rows, {len(df_info.columns)} columns")

        if st.button("\U0001F4DA Concatenate", type="primary", key="btn_concat"):
            if len(selected_datasets) < 2:
                st.warning("Please select at least 2 datasets.")
            else:
                try:
                    df_list = [datasets[name] for name in selected_datasets]
                    result = concat_datasets(df_list, axis=axis)
                    st.session_state["_concat_preview"] = result
                    st.success(f"Concatenation complete! Result: {len(result):,} rows, {len(result.columns)} columns")
                except Exception as e:
                    st.error(f"Concatenation failed: {str(e)}")

        # Preview and save
        if "_concat_preview" in st.session_state and st.session_state["_concat_preview"] is not None:
            preview_df = st.session_state["_concat_preview"]
            st.markdown("#### Preview (first 100 rows)")
            st.dataframe(preview_df.head(100), use_container_width=True)

            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.button("\U0001F4BE Save to Session", key="save_concat_result"):
                    st.session_state.concat_result_df = preview_df.copy()
                    st.session_state.merged_df = preview_df.copy()
                    st.success("Saved as 'Concat Result' and 'Merged Data' - available across all pages!")
