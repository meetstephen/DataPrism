"""Data cleaning engine with undo/redo support and audit logging."""
import streamlit as st
import pandas as pd
from datetime import datetime


def init_cleaning_state():
    """Initialize cleaning session state keys. Call from app.py."""
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None
    if "working_df" not in st.session_state:
        st.session_state.working_df = None
    if "cleaning_log" not in st.session_state:
        st.session_state.cleaning_log = []
    if "cleaning_history" not in st.session_state:
        st.session_state.cleaning_history = []


def apply_cleaning_step(action_name: str, action_fn, *args, **kwargs):
    """Apply a cleaning operation with undo snapshot and logging."""
    st.session_state.cleaning_history.append(st.session_state.working_df.copy())
    result_df, rows_affected = action_fn(st.session_state.working_df, *args, **kwargs)
    st.session_state.working_df = result_df
    st.session_state.cleaning_log.append({
        "step": len(st.session_state.cleaning_log) + 1,
        "action": action_name,
        "rows_affected": rows_affected,
        "timestamp": datetime.utcnow().isoformat(),
    })
    return rows_affected


# --- Cleaning Operations ---
def drop_missing_rows(df, columns):
    before = len(df)
    result = df.dropna(subset=columns)
    return result, before - len(result)


def fill_missing(df, column, strategy="mean"):
    df = df.copy()
    count = int(df[column].isna().sum())
    if strategy == "mean":
        df[column] = df[column].fillna(df[column].mean())
    elif strategy == "median":
        df[column] = df[column].fillna(df[column].median())
    elif strategy == "mode":
        df[column] = df[column].fillna(df[column].mode().iloc[0] if not df[column].mode().empty else 0)
    elif strategy == "zero":
        df[column] = df[column].fillna(0)
    elif strategy == "forward":
        df[column] = df[column].ffill()
    elif strategy == "backward":
        df[column] = df[column].bfill()
    return df, count


def remove_duplicates(df, keep="first"):
    before = len(df)
    result = df.drop_duplicates(keep=keep)
    return result, before - len(result)


def remove_outliers_iqr(df, column, multiplier=1.5):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    before = len(df)
    result = df[(df[column] >= lower) & (df[column] <= upper)]
    return result, before - len(result)


def drop_columns(df, columns):
    result = df.drop(columns=columns)
    return result, 0


def rename_columns(df, rename_map):
    result = df.rename(columns=rename_map)
    return result, 0



def add_calculated_column(df, new_col_name, expression):
    """Add a new column computed from a pandas arithmetic expression.

    Uses ``DataFrame.eval`` with the (safe) Python engine, which supports
    arithmetic (+ - * / // % **), comparison and boolean operators referencing
    existing columns. Column names containing spaces must be wrapped in
    backticks, e.g. ``\u0060Course Cost\u0060 * 1.1``. Arbitrary function calls
    and attribute access are not permitted, keeping evaluation safe.

    Returns (new_df, rows_affected).
    """
    df = df.copy()
    result = df.eval(expression, engine="python")
    df[new_col_name] = result
    return df, len(df)


def build_arithmetic_expression(left, operator, right, right_is_column=True):
    """Build a safe DataFrame.eval expression from a guided arithmetic builder.

    Args:
        left: Left-hand column name.
        operator: One of + - * / (also accepts the wrapped operands as-is).
        right: Right-hand column name or scalar value.
        right_is_column: If True, ``right`` is treated as a column name;
            otherwise it is treated as a literal numeric value.

    Returns the expression string suitable for ``add_calculated_column``.
    """
    def _wrap(name):
        # Backtick-quote identifiers so names with spaces/special chars work.
        return f"`{name}`"

    left_token = _wrap(left)
    right_token = _wrap(right) if right_is_column else f"{right}"
    return f"{left_token} {operator} {right_token}"


# --- Enterprise Cleaning Operations ---

def flag_missing(df, columns):
    """Add boolean flag columns indicating missing values.

    For each column in `columns`, creates a new column `{col}_is_missing`.
    Returns (df, rows_affected) where rows_affected is total flagged cells.
    """
    df = df.copy()
    total_flagged = 0
    for col in columns:
        flag_col = f"{col}_is_missing"
        df[flag_col] = df[col].isnull()
        total_flagged += int(df[flag_col].sum())
    return df, total_flagged


def cap_outliers(df, column, method="iqr", multiplier=1.5):
    """Cap (winsorize) outliers instead of removing them.

    Values below the lower bound are set to the lower bound; values above
    the upper bound are set to the upper bound.
    Returns (df, rows_affected).
    """
    df = df.copy()
    if method == "iqr":
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR
    else:
        # Percentile method
        lower = df[column].quantile(0.01)
        upper = df[column].quantile(0.99)

    mask = (df[column] < lower) | (df[column] > upper)
    rows_affected = int(mask.sum())
    df[column] = df[column].clip(lower=lower, upper=upper)
    return df, rows_affected


def split_column(df, column, delimiter=",", new_col_names=None):
    """Split a text column into multiple columns by delimiter.

    Returns (df, rows_affected).
    """
    df = df.copy()
    split_result = df[column].astype(str).str.split(delimiter, expand=True)
    n_new_cols = split_result.shape[1]

    if new_col_names and len(new_col_names) >= n_new_cols:
        names = new_col_names[:n_new_cols]
    else:
        names = [f"{column}_part{i+1}" for i in range(n_new_cols)]

    for i, name in enumerate(names):
        df[name] = split_result[i].str.strip() if split_result[i] is not None else None

    rows_affected = int(df[column].notna().sum())
    return df, rows_affected


def merge_columns(df, columns, new_col_name, separator=" "):
    """Merge multiple columns into one by concatenating their string values.

    Returns (df, rows_affected).
    """
    df = df.copy()
    df[new_col_name] = df[columns].astype(str).agg(separator.join, axis=1)
    rows_affected = len(df)
    return df, rows_affected


def standardize_text(df, column, method="lowercase"):
    """Standardize text in a column.

    Methods: lowercase, uppercase, titlecase, strip, strip_all.
    Returns (df, rows_affected).
    """
    df = df.copy()
    series = df[column]
    rows_affected = int(series.notna().sum())

    if method == "lowercase":
        df[column] = series.astype(str).str.lower()
    elif method == "uppercase":
        df[column] = series.astype(str).str.upper()
    elif method == "titlecase":
        df[column] = series.astype(str).str.title()
    elif method == "strip":
        df[column] = series.astype(str).str.strip()
    elif method == "strip_all":
        df[column] = series.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    return df, rows_affected


def convert_column_type(df, column, target_type):
    """Convert a column to a different data type.

    Supported target_type: 'numeric', 'text', 'datetime', 'integer', 'float'.
    Returns (df, rows_affected).
    """
    df = df.copy()
    rows_affected = int(df[column].notna().sum())

    if target_type == "numeric":
        df[column] = pd.to_numeric(df[column], errors="coerce")
    elif target_type == "integer":
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].astype("Int64")
    elif target_type == "float":
        df[column] = pd.to_numeric(df[column], errors="coerce").astype(float)
    elif target_type == "text":
        df[column] = df[column].astype(str)
    elif target_type == "datetime":
        df[column] = pd.to_datetime(df[column], errors="coerce")

    return df, rows_affected
