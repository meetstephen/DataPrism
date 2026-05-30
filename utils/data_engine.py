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
