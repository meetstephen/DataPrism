"""SQL query engine for running SQL against in-memory DataFrames using pandasql."""
import re
import time
import streamlit as st
import pandas as pd
from pandasql import sqldf


# Example queries for user reference
EXAMPLE_QUERIES = [
    "SELECT * FROM builtin LIMIT 10",
    "SELECT column_name, COUNT(*) as cnt FROM builtin GROUP BY column_name ORDER BY cnt DESC",
    "SELECT * FROM uploaded WHERE rowid <= 50",
    "SELECT a.*, b.column_name FROM builtin a LEFT JOIN uploaded b ON a.id = b.id",
    "SELECT COUNT(*) as total_rows, COUNT(DISTINCT column_name) as unique_vals FROM builtin",
]


def get_sql_tables():
    """Build dict from session state mapping friendly table names to DataFrames.

    Returns
    -------
    dict of {str: pd.DataFrame}
    """
    key_map = {
        "builtin": "df",
        "uploaded": "uploaded_df",
        "online": "online_df",
        "cleaned": "working_df",
        "merged": "merged_df",
        "sql_result": "sql_result_df",
    }
    tables = {}
    for table_name, session_key in key_map.items():
        df = st.session_state.get(session_key)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            tables[table_name] = df
    return tables


def _validate_query(query):
    """Validate that a query is a read-only SELECT or WITH statement.

    Rejects dangerous statements like ATTACH DATABASE, PRAGMA, INSERT, etc.

    Returns None if valid, or an error string if rejected.
    """
    # Strip leading whitespace and SQL comments (-- line comments, /* block */)
    stripped = query.strip()
    stripped = re.sub(r"--[^\n]*", "", stripped)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    stripped = stripped.strip()

    if not stripped:
        return "Empty query."

    # Only allow queries starting with SELECT or WITH (CTEs)
    first_keyword = stripped.split()[0].upper() if stripped.split() else ""
    if first_keyword not in ("SELECT", "WITH"):
        return (
            f"Only SELECT and WITH (CTE) queries are allowed. "
            f"Got: '{first_keyword}'. Statements like ATTACH DATABASE, PRAGMA, "
            f"INSERT, UPDATE, DELETE, DROP, and CREATE are blocked for security."
        )
    return None


def run_sql_query(query, tables_dict):
    """Execute a SQL query against provided DataFrames.

    Parameters
    ----------
    query : str - SQL query string
    tables_dict : dict - mapping of table names to DataFrames

    Returns
    -------
    tuple of (result_df, execution_time_seconds, error_string_or_none)
    """
    # Guard: only allow SELECT/WITH queries to prevent filesystem access via SQLite
    validation_error = _validate_query(query)
    if validation_error:
        return pd.DataFrame(), 0.0, validation_error

    # Make table names available as local variables for pandasql
    local_env = dict(tables_dict)

    start = time.time()
    try:
        result_df = sqldf(query, local_env)
        elapsed = time.time() - start
        return result_df, elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        return pd.DataFrame(), elapsed, str(e)
