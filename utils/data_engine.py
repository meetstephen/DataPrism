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


# --- Additional Cleaning Operations ---

def flag_missing(df, column):
    """Add a boolean '{column}_is_missing' column indicating missing values.
    Returns (df, count_flagged).
    """
    df = df.copy()
    flag_col = f"{column}_is_missing"
    df[flag_col] = df[column].isna()
    count_flagged = int(df[flag_col].sum())
    return df, count_flagged


def cap_outliers(df, column, multiplier=1.5):
    """Clip values to IQR bounds instead of removing rows.
    Returns (df, count_capped).
    """
    df = df.copy()
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    before = df[column].copy()
    df[column] = df[column].clip(lower=lower, upper=upper)
    count_capped = int((before != df[column]).sum())
    return df, count_capped


def split_column(df, column, delimiter, new_col_names):
    """Split a text column into multiple new columns by delimiter.
    Returns (df, 0) since no rows are affected - only structure changes.
    """
    df = df.copy()
    split_data = df[column].astype(str).str.split(delimiter, expand=True)

    # Assign new column names (use as many as provided)
    for i, name in enumerate(new_col_names):
        if i < split_data.shape[1]:
            df[name] = split_data[i].str.strip()
        else:
            df[name] = None

    return df, 0


def merge_columns(df, columns, separator, new_col_name):
    """Concatenate multiple text columns into one new column.
    Returns (df, 0) since no rows are affected - only structure changes.
    """
    df = df.copy()
    df[new_col_name] = df[columns].astype(str).agg(separator.join, axis=1)
    return df, 0


def standardize_text(df, column, mode='lowercase'):
    """Apply text transformations to a column.
    Modes: lowercase, uppercase, title, strip.
    Returns (df, rows_affected).
    """
    df = df.copy()
    non_null_count = int(df[column].notna().sum())

    if mode == 'lowercase':
        df[column] = df[column].astype(str).str.lower()
    elif mode == 'uppercase':
        df[column] = df[column].astype(str).str.upper()
    elif mode == 'title':
        df[column] = df[column].astype(str).str.title()
    elif mode == 'strip':
        df[column] = df[column].astype(str).str.strip()

    return df, non_null_count


def convert_column_type(df, column, target_type):
    """Convert a column to a different dtype.
    target_type: 'numeric', 'datetime', 'string', 'category'.
    Returns (df, rows_affected) where rows_affected is the count of successfully converted values.
    """
    df = df.copy()
    original_non_null = int(df[column].notna().sum())

    if target_type == 'numeric':
        df[column] = pd.to_numeric(df[column], errors='coerce')
    elif target_type == 'datetime':
        df[column] = pd.to_datetime(df[column], errors='coerce')
    elif target_type == 'string':
        df[column] = df[column].astype(str)
    elif target_type == 'category':
        df[column] = df[column].astype('category')

    new_non_null = int(df[column].notna().sum())
    return df, new_non_null
