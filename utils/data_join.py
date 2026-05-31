"""Data joining and merging utilities for combining multiple datasets."""
import streamlit as st
import pandas as pd


def get_available_datasets():
    """Read session state and return dict of {name: DataFrame} for all loaded datasets.

    Checks standard session state keys and returns only non-None DataFrames.
    """
    key_map = {
        "Built-in Data": "df",
        "Uploaded Data": "uploaded_df",
        "Online Data": "online_df",
        "Cleaned Data": "working_df",
        "Merged Data": "merged_df",
        "SQL Result": "sql_result_df",
    }
    datasets = {}
    for friendly_name, key in key_map.items():
        df = st.session_state.get(key)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            datasets[friendly_name] = df
    return datasets


def join_datasets(left_df, right_df, left_key, right_key, join_type="inner"):
    """Perform a merge/join of two DataFrames.

    Parameters
    ----------
    left_df : pd.DataFrame
    right_df : pd.DataFrame
    left_key : str - column name in left_df to join on
    right_key : str - column name in right_df to join on
    join_type : str - one of 'inner', 'left', 'right', 'outer'

    Returns
    -------
    pd.DataFrame - the merged result
    """
    valid_types = ("inner", "left", "right", "outer")
    if join_type not in valid_types:
        raise ValueError(f"join_type must be one of {valid_types}, got '{join_type}'")

    result = pd.merge(
        left_df,
        right_df,
        left_on=left_key,
        right_on=right_key,
        how=join_type,
        suffixes=("_left", "_right"),
    )
    return result


def concat_datasets(df_list, axis=0):
    """Concatenate a list of DataFrames vertically (axis=0) or horizontally (axis=1).

    Parameters
    ----------
    df_list : list of pd.DataFrame
    axis : int - 0 for vertical stacking, 1 for horizontal

    Returns
    -------
    pd.DataFrame - the concatenated result
    """
    if not df_list:
        return pd.DataFrame()
    result = pd.concat(df_list, axis=axis, ignore_index=True)
    return result
