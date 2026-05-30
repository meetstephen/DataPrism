"""Session persistence utilities for DataPrism.

Saves and restores critical session state to disk so user work survives
page refreshes and app reboots.
"""

import os
import json
import datetime
import streamlit as st

SESSION_DIR = os.path.join(".dataprism", "sessions", "default_session")


def _ensure_session_dir():
    """Create the session directory if it does not exist."""
    try:
        os.makedirs(SESSION_DIR, exist_ok=True)
    except Exception:
        pass


def save_dataframe(df, name):
    """Save a DataFrame to parquet (with CSV fallback)."""
    try:
        _ensure_session_dir()
        parquet_path = os.path.join(SESSION_DIR, f"{name}.parquet")
        df.to_parquet(parquet_path, index=False)
    except Exception:
        try:
            csv_path = os.path.join(SESSION_DIR, f"{name}.csv")
            df.to_csv(csv_path, index=False)
        except Exception:
            pass


def load_dataframe(name):
    """Load a DataFrame from parquet or CSV."""
    import pandas as pd

    parquet_path = os.path.join(SESSION_DIR, f"{name}.parquet")
    csv_path = os.path.join(SESSION_DIR, f"{name}.csv")
    try:
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        elif os.path.exists(csv_path):
            return pd.read_csv(csv_path)
    except Exception:
        pass
    return None


def save_json(data, name):
    """Save a dict or list as JSON."""
    try:
        _ensure_session_dir()
        path = os.path.join(SESSION_DIR, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception:
        pass


def load_json(name):
    """Load JSON data from file."""
    path = os.path.join(SESSION_DIR, f"{name}.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_text(text, name):
    """Save text content to a file."""
    try:
        _ensure_session_dir()
        path = os.path.join(SESSION_DIR, f"{name}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def load_text(name):
    """Load text content from a file."""
    path = os.path.join(SESSION_DIR, f"{name}.txt")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return None


def save_session_state():
    """Persist all critical session state to disk."""
    try:
        _ensure_session_dir()

        # Save DataFrames
        if st.session_state.get("uploaded_df") is not None:
            save_dataframe(st.session_state.uploaded_df, "uploaded_df")
        if st.session_state.get("online_df") is not None:
            save_dataframe(st.session_state.online_df, "online_df")
        if st.session_state.get("working_df") is not None:
            save_dataframe(st.session_state.working_df, "working_df")
        if st.session_state.get("raw_df") is not None:
            save_dataframe(st.session_state.raw_df, "raw_df")

        # Save chat histories
        chat_history = st.session_state.get("chat_history", [])
        if chat_history:
            # Strip non-serializable figure objects
            serializable_history = []
            for msg in chat_history:
                entry = {"role": msg.get("role", ""), "content": msg.get("content", "")}
                serializable_history.append(entry)
            save_json(serializable_history, "chat_history")

        doc_chat_history = st.session_state.get("doc_chat_history", [])
        if doc_chat_history:
            save_json(doc_chat_history, "doc_chat_history")

        # Save cleaning log
        cleaning_log = st.session_state.get("cleaning_log", [])
        if cleaning_log:
            save_json(cleaning_log, "cleaning_log")

        # Save document content
        doc_content = st.session_state.get("doc_content")
        if doc_content:
            save_text(doc_content, "doc_content")

        # Save metadata
        metadata = {}
        if st.session_state.get("doc_name"):
            metadata["doc_name"] = st.session_state.doc_name
        if st.session_state.get("online_data_source"):
            metadata["online_data_source"] = st.session_state.online_data_source
        metadata["last_saved"] = datetime.datetime.now().isoformat()
        save_json(metadata, "metadata")

    except Exception:
        pass


def restore_session_state():
    """Restore persisted session state on startup. Returns True if anything was restored."""
    try:
        metadata = load_json("metadata")
        if metadata is None:
            return False

        restored = False

        # Restore DataFrames
        if st.session_state.get("uploaded_df") is None:
            df = load_dataframe("uploaded_df")
            if df is not None:
                st.session_state.uploaded_df = df
                restored = True

        if st.session_state.get("online_df") is None:
            df = load_dataframe("online_df")
            if df is not None:
                st.session_state.online_df = df
                restored = True

        if st.session_state.get("working_df") is None:
            df = load_dataframe("working_df")
            if df is not None:
                st.session_state.working_df = df
                restored = True

        if st.session_state.get("raw_df") is None:
            df = load_dataframe("raw_df")
            if df is not None:
                st.session_state.raw_df = df
                restored = True

        # Restore chat histories
        if not st.session_state.get("chat_history"):
            chat_history = load_json("chat_history")
            if chat_history:
                st.session_state.chat_history = chat_history
                restored = True

        if not st.session_state.get("doc_chat_history"):
            doc_chat_history = load_json("doc_chat_history")
            if doc_chat_history:
                st.session_state.doc_chat_history = doc_chat_history
                restored = True

        # Restore cleaning log
        if not st.session_state.get("cleaning_log"):
            cleaning_log = load_json("cleaning_log")
            if cleaning_log:
                st.session_state.cleaning_log = cleaning_log
                restored = True

        # Restore document content
        if not st.session_state.get("doc_content"):
            doc_content = load_text("doc_content")
            if doc_content:
                st.session_state.doc_content = doc_content
                restored = True

        # Restore metadata fields
        if not st.session_state.get("doc_name") and metadata.get("doc_name"):
            st.session_state.doc_name = metadata["doc_name"]
            restored = True
        if not st.session_state.get("online_data_source") and metadata.get("online_data_source"):
            st.session_state.online_data_source = metadata["online_data_source"]
            restored = True

        return restored
    except Exception:
        return False


def clear_persisted_session():
    """Remove the session directory and all saved data."""
    import shutil

    try:
        if os.path.exists(SESSION_DIR):
            shutil.rmtree(SESSION_DIR)
    except Exception:
        pass


def get_last_saved_time():
    """Return the ISO timestamp of the last save, or None."""
    try:
        metadata = load_json("metadata")
        if metadata:
            return metadata.get("last_saved")
    except Exception:
        pass
    return None
