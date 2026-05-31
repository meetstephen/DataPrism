"""Shared data loading helpers to ensure datasets are always available."""
import os
import streamlit as st
import pandas as pd


def ensure_builtin_data():
    """Ensure the built-in community college dataset is loaded into session state.
    Safe to call from any page. Returns the DataFrame."""
    if st.session_state.get("df") is not None:
        return st.session_state.df
    data_path = "data/community_college_data.csv"
    try:
        if os.path.exists(data_path):
            st.session_state.df = pd.read_csv(data_path)
        else:
            from utils.data_generator import save_dataset
            st.session_state.df = save_dataset(data_path)
    except Exception:
        # Last resort: generate in-memory
        from utils.data_generator import generate_dataset
        st.session_state.df = generate_dataset()
    return st.session_state.df


def init_all_session_state():
    """Initialize all common session state keys. Safe to call from any page."""
    defaults = {
        "online_df": None,
        "uploaded_df": None,
        "working_df": None,
        "raw_df": None,
        "generated_report": None,
        "chat_history": [],
        "doc_chat_history": [],
        "doc_content": None,
        "doc_name": None,
        "gemini_api_key": None,
        "cleaning_log": [],
        "cleaning_history": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
