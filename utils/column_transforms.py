"""Column transformation utilities for the Data Cleaning page.

Each function accepts a DataFrame and returns a (df, rows_affected) tuple,
compatible with apply_cleaning_step() from utils/data_engine.py.
"""

import pandas as pd
import numpy as np
import re


def extract_date_parts(df, column):
    """Extract year, month, day, and day_of_week from a datetime column.

    Creates new columns: {column}_year, {column}_month, {column}_day, {column}_weekday.

    Args:
        df: Input DataFrame.
        column: Name of a datetime-compatible column.

    Returns:
        (df, rows_affected) tuple.
    """
    df = df.copy()
    dt_series = pd.to_datetime(df[column], errors="coerce")
    df[f"{column}_year"] = dt_series.dt.year
    df[f"{column}_month"] = dt_series.dt.month
    df[f"{column}_day"] = dt_series.dt.day
    df[f"{column}_weekday"] = dt_series.dt.day_name()
    rows_affected = int(dt_series.notna().sum())
    return df, rows_affected


def bin_numeric(df, column, n_bins=5, labels=None):
    """Bin a numeric column into equal-width intervals.

    Creates a new column: {column}_binned.

    Args:
        df: Input DataFrame.
        column: Name of a numeric column.
        n_bins: Number of bins (default 5).
        labels: Optional list of labels for bins.

    Returns:
        (df, rows_affected) tuple.
    """
    df = df.copy()
    valid_mask = df[column].notna()
    if labels and len(labels) != n_bins:
        labels = None
    df[f"{column}_binned"] = pd.cut(df[column], bins=n_bins, labels=labels)
    rows_affected = int(valid_mask.sum())
    return df, rows_affected


def one_hot_encode(df, column, drop_original=False):
    """One-hot encode a categorical column using pd.get_dummies.

    Args:
        df: Input DataFrame.
        column: Name of a categorical/object column.
        drop_original: If True, drop the original column after encoding.

    Returns:
        (df, rows_affected) tuple.
    """
    dummies = pd.get_dummies(df[column], prefix=column, dtype=int)
    rows_affected = int(len(dummies))
    df = pd.concat([df, dummies], axis=1)
    if drop_original:
        df = df.drop(columns=[column])
    return df, rows_affected


def string_operations(df, column, operation, pattern=None):
    """Perform string operations on a text column.

    Supported operations: 'lowercase', 'uppercase', 'trim', 'extract_regex'.

    Args:
        df: Input DataFrame.
        column: Name of a text column.
        operation: One of 'lowercase', 'uppercase', 'trim', 'extract_regex'.
        pattern: Regex pattern (required for 'extract_regex').

    Returns:
        (df, rows_affected) tuple.
    """
    df = df.copy()
    valid_mask = df[column].notna()
    rows_affected = int(valid_mask.sum())

    if operation == "lowercase":
        df[column] = df[column].astype(str).str.lower()
    elif operation == "uppercase":
        df[column] = df[column].astype(str).str.upper()
    elif operation == "trim":
        df[column] = df[column].astype(str).str.strip()
    elif operation == "extract_regex":
        if not pattern:
            return df, 0
        # Guard: limit pattern length to prevent catastrophic backtracking
        MAX_PATTERN_LENGTH = 200
        if len(pattern) > MAX_PATTERN_LENGTH:
            return df, 0
        # Validate pattern with re.compile before applying to the DataFrame
        try:
            re.compile(pattern)
        except re.error:
            return df, 0
        try:
            extracted = df[column].astype(str).str.extract(f"({pattern})", expand=False)
        except Exception:
            return df, 0
        df[f"{column}_extracted"] = extracted
        rows_affected = int(extracted.notna().sum())
    else:
        rows_affected = 0

    return df, rows_affected
