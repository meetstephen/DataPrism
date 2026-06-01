"""
SQL Query Interface - Run SQL queries against your loaded datasets.
"""

import streamlit as st
st.set_page_config(page_title="SQL Query Interface", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_sidebar_nav
inject_global_css()
render_sidebar_nav()
from utils.data_loader import ensure_builtin_data
ensure_builtin_data()

import pandas as pd
from utils.sql_engine import get_sql_tables, run_sql_query, EXAMPLE_QUERIES

st.title("\U0001F4DD SQL Query Interface")
st.markdown("Write and execute SQL queries against your loaded datasets.")

with st.expander("❓ How to use this page", expanded=False):
    st.markdown("""
    1. Your loaded datasets appear as SQL tables (e.g. `builtin`, `uploaded`, `cleaned`)
    2. Write any **SELECT** query using standard SQL (SQLite dialect)
    3. Click **Run Query** to see results with execution time
    4. **Save Result** stores the output as a new dataset for use elsewhere
    5. Only read queries are allowed (INSERT/DELETE/DROP are blocked for safety)
    """)

# --- Direct file upload option ---
with st.expander("\U0001F4C1 Upload your own file directly", expanded=False):
    sql_file = st.file_uploader(
        "Upload CSV, Excel, JSON, TSV, or Parquet",
        type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
        key="sql_file_upload",
        help="File will also be saved to your session for use on other pages.",
    )
    if sql_file is not None:
        from utils.data_loader import load_file_flexible
        loaded, err = load_file_flexible(sql_file)
        if err:
            st.error(err)
        elif loaded is not None:
            st.session_state.uploaded_df = loaded.copy()
            st.success(f"Loaded: {sql_file.name} ({len(loaded):,} rows)")

st.markdown("---")

# Get available tables
tables = get_sql_tables()

if not tables:
    st.warning("No datasets available. Please load data first using the Upload & Analyze page or the file uploader above.")
    st.stop()

# --- Show available tables ---
st.subheader("\U0001F4CA Available Tables")
table_cols = st.columns(min(len(tables), 3))
for idx, (table_name, table_df) in enumerate(tables.items()):
    with table_cols[idx % 3]:
        st.markdown(f"**`{table_name}`**")
        st.caption(f"{len(table_df):,} rows, {len(table_df.columns)} columns")
        st.code(", ".join(table_df.columns.tolist()[:10]) + ("..." if len(table_df.columns) > 10 else ""), language=None)

st.markdown("---")

# --- SQL Query Input ---
st.subheader("\U0001F4DD Write Your Query")

query = st.text_area(
    "SQL Query",
    value="SELECT * FROM builtin LIMIT 10",
    height=150,
    help="Use table names shown above. Standard SQL syntax supported (SQLite dialect).",
    key="sql_query_input",
)

col_run, col_clear = st.columns([1, 4])
with col_run:
    run_clicked = st.button("\U000025B6\U0000FE0F Run Query", type="primary", key="btn_run_sql")

# --- Execute Query ---
if run_clicked:
    if not query.strip():
        st.warning("Please enter a SQL query.")
    else:
        with st.spinner("Executing query..."):
            result_df, exec_time, error = run_sql_query(query, tables)

        if error:
            st.error(f"Query Error: {error}")
            st.info("Check table names and column names above. Use SQLite SQL dialect.")
        else:
            st.session_state["_sql_result"] = result_df
            st.session_state["_sql_exec_time"] = exec_time

# --- Display Results ---
if "_sql_result" in st.session_state and st.session_state["_sql_result"] is not None:
    result_df = st.session_state["_sql_result"]
    exec_time = st.session_state.get("_sql_exec_time", 0)

    st.markdown("---")
    st.subheader("\U0001F4CB Results")

    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
    with col_metrics1:
        st.metric("Rows", f"{len(result_df):,}")
    with col_metrics2:
        st.metric("Columns", f"{len(result_df.columns)}")
    with col_metrics3:
        st.metric("Execution Time", f"{exec_time:.4f}s")

    st.dataframe(result_df, use_container_width=True)

    # Save result button
    col_save1, col_save2 = st.columns([1, 3])
    with col_save1:
        if st.button("\U0001F4BE Save Result", key="save_sql_result"):
            st.session_state.sql_result_df = result_df.copy()
            st.success("Saved as 'SQL Result' - available across all pages!")

# --- Example Queries ---
with st.expander("\U0001F4A1 Example Queries", expanded=False):
    st.markdown("Click to copy any example query:")
    for i, example in enumerate(EXAMPLE_QUERIES):
        # Adjust example to use actual available table names
        st.code(example, language="sql")
    st.caption("Note: Replace column names with actual columns from your datasets.")
