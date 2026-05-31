"""Data Dictionary - Auto-generate and manage column documentation."""
import streamlit as st
st.set_page_config(page_title="Data Dictionary", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()
from utils.data_loader import ensure_builtin_data
ensure_builtin_data()

import pandas as pd
from utils.data_generator import generate_dataset

st.title("\U0001F4D6 Data Dictionary")
st.markdown("Auto-generate column documentation and add your own descriptions for each column.")

with st.expander("❓ How to use this page", expanded=False):
    st.markdown("""
    1. Select a dataset to document
    2. **Column Information** is auto-generated (type, nulls, uniques, samples)
    3. **Add descriptions** for each column in the text fields below
    4. **Export** as Markdown or CSV to share with your team
    """)

# --- Data Source Selection ---
if "df" not in st.session_state:
    st.session_state.df = generate_dataset()

data_source_options = ["Built-in Community College Data"]
if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    data_source_options.append("Uploaded Data")
if "online_df" in st.session_state and st.session_state.online_df is not None:
    data_source_options.append("Online Data")
if "working_df" in st.session_state and st.session_state.working_df is not None:
    data_source_options.append("Cleaned Data")

data_source = st.radio("Select Data Source:", data_source_options, horizontal=True, key="dd_source")

# Direct upload option
with st.expander("\U0001F4C1 Upload your own file directly", expanded=False):
    dd_file = st.file_uploader(
        "Upload CSV, Excel, JSON, TSV, or Parquet",
        type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
        key="dd_file_upload",
        help="File will also be saved to your session for use on other pages.",
    )
    if dd_file is not None:
        from utils.data_loader import load_file_flexible
        loaded, err = load_file_flexible(dd_file)
        if err:
            st.error(err)
        elif loaded is not None:
            st.session_state.uploaded_df = loaded.copy()
            st.success(f"Loaded: {dd_file.name} ({len(loaded):,} rows)")

if data_source == "Built-in Community College Data":
    df = st.session_state.df.copy()
    dataset_name = "builtin"
elif data_source == "Uploaded Data":
    df = st.session_state.uploaded_df.copy()
    dataset_name = "uploaded"
elif data_source == "Online Data":
    df = st.session_state.online_df.copy()
    dataset_name = "online"
elif data_source == "Cleaned Data":
    df = st.session_state.working_df.copy()
    dataset_name = "cleaned"
else:
    df = st.session_state.df.copy()
    dataset_name = "builtin"

st.info(f"Working with: {len(df):,} rows, {len(df.columns)} columns")
st.markdown("---")

# --- Initialize Data Dictionary in session state ---
if "dp_data_dictionary" not in st.session_state:
    st.session_state.dp_data_dictionary = {}

if dataset_name not in st.session_state.dp_data_dictionary:
    st.session_state.dp_data_dictionary[dataset_name] = {}

descriptions = st.session_state.dp_data_dictionary[dataset_name]

# --- Auto-generate column info ---
st.markdown("### Column Information")

col_info = []
for col in df.columns:
    non_null = int(df[col].notna().sum())
    unique_count = int(df[col].nunique())
    sample_vals = df[col].dropna().head(3).tolist()
    sample_str = ", ".join(str(v) for v in sample_vals)
    if len(sample_str) > 80:
        sample_str = sample_str[:77] + "..."
    col_info.append({
        "Column": col,
        "Data Type": str(df[col].dtype),
        "Non-Null Count": f"{non_null:,} / {len(df):,}",
        "Unique Values": unique_count,
        "Sample Values": sample_str,
    })

info_df = pd.DataFrame(col_info)
st.dataframe(info_df, use_container_width=True, hide_index=True)

# --- Editable Descriptions ---
st.markdown("---")
st.markdown("### Column Descriptions")
st.markdown("Add your own descriptions for each column below. These are saved in your session.")

for col in df.columns:
    current_desc = descriptions.get(col, "")
    new_desc = st.text_input(
        f"**{col}** ({df[col].dtype})",
        value=current_desc,
        key=f"dd_desc_{dataset_name}_{col}",
        placeholder="Enter a description for this column...",
    )
    if new_desc != current_desc:
        st.session_state.dp_data_dictionary[dataset_name][col] = new_desc

# --- Export Options ---
st.markdown("---")
st.markdown("### Export Data Dictionary")

export_col1, export_col2 = st.columns(2)

with export_col1:
    # Export as Markdown
    md_lines = [f"# Data Dictionary - {dataset_name}\n"]
    md_lines.append(f"**Rows:** {len(df):,} | **Columns:** {len(df.columns)}\n")
    md_lines.append("| Column | Type | Non-Null | Unique | Description |")
    md_lines.append("|--------|------|----------|--------|-------------|")
    for info in col_info:
        desc = descriptions.get(info["Column"], "")
        md_lines.append(
            f"| {info['Column']} | {info['Data Type']} | {info['Non-Null Count']} "
            f"| {info['Unique Values']} | {desc} |"
        )
    md_content = "\n".join(md_lines)
    st.download_button(
        "\U0001F4DD Download as Markdown",
        md_content,
        file_name="data_dictionary.md",
        mime="text/markdown",
        use_container_width=True,
    )

with export_col2:
    # Export as CSV
    export_rows = []
    for info in col_info:
        export_rows.append({
            "Column": info["Column"],
            "Data Type": info["Data Type"],
            "Non-Null Count": info["Non-Null Count"],
            "Unique Values": info["Unique Values"],
            "Sample Values": info["Sample Values"],
            "Description": descriptions.get(info["Column"], ""),
        })
    export_df = pd.DataFrame(export_rows)
    csv_content = export_df.to_csv(index=False)
    st.download_button(
        "\U0001F4C4 Download as CSV",
        csv_content,
        file_name="data_dictionary.csv",
        mime="text/csv",
        use_container_width=True,
    )
