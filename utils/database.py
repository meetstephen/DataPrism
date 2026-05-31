"""Data-access layer for DataPrism's optional Supabase cloud persistence.

Every function returns a ``(ok, payload)`` tuple:
    ok == True  -> payload is the result (list/DataFrame/str/message)
    ok == False -> payload is a user-facing error string

All functions are safe to call even when Supabase is not configured; they
simply return ``(False, <reason>)`` so the UI can show a friendly message.

Tables (created via SUPABASE_SETUP.md):
    dp_datasets, dp_reports, dp_validation_rule_sets, dp_insights
"""

import io

import pandas as pd
import streamlit as st

from utils.supabase_client import get_client


def _get_user_id():
    """Return the current user_id from session state, or None."""
    return st.session_state.get("dp_user_id")


def _is_admin():
    """Return True if the current user has admin role."""
    return st.session_state.get("dp_user_role") == "admin"

# Table names
T_DATASETS = "dp_datasets"
T_REPORTS = "dp_reports"
T_RULE_SETS = "dp_validation_rule_sets"
T_INSIGHTS = "dp_insights"


# --- Datasets ---------------------------------------------------------------

def save_dataset(name, df, description=""):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        payload = {
            "name": name,
            "description": description or "",
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": [str(c) for c in df.columns],
            "data_csv": df.to_csv(index=False),
        }
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user":
            payload["user_id"] = user_id
        client.table(T_DATASETS).insert(payload).execute()
        return True, f"Saved dataset '{name}' ({len(df):,} rows)."
    except Exception as e:
        return False, f"Could not save dataset: {e}"


def list_datasets():
    client, err = get_client()
    if client is None:
        return False, err
    try:
        query = (
            client.table(T_DATASETS)
            .select("id,name,description,row_count,column_count,created_at")
            .order("created_at", desc=True)
        )
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user" and not _is_admin():
            query = query.eq("user_id", user_id)
        res = query.execute()
        return True, res.data or []
    except Exception as e:
        return False, f"Could not list datasets: {e}"


def get_dataset(dataset_id):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        res = (
            client.table(T_DATASETS)
            .select("name,data_csv")
            .eq("id", dataset_id)
            .single()
            .execute()
        )
        df = pd.read_csv(io.StringIO(res.data["data_csv"]))
        return True, df
    except Exception as e:
        return False, f"Could not load dataset: {e}"


def delete_dataset(dataset_id):
    return _delete(T_DATASETS, dataset_id, "dataset")


# --- Reports ----------------------------------------------------------------

def save_report(title, html, dataset_name=""):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        payload = {"title": title, "html": html, "dataset_name": dataset_name or ""}
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user":
            payload["user_id"] = user_id
        client.table(T_REPORTS).insert(payload).execute()
        return True, f"Saved report '{title}'."
    except Exception as e:
        return False, f"Could not save report: {e}"


def list_reports():
    client, err = get_client()
    if client is None:
        return False, err
    try:
        query = (
            client.table(T_REPORTS)
            .select("id,title,dataset_name,created_at")
            .order("created_at", desc=True)
        )
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user" and not _is_admin():
            query = query.eq("user_id", user_id)
        res = query.execute()
        return True, res.data or []
    except Exception as e:
        return False, f"Could not list reports: {e}"


def get_report(report_id):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        res = (
            client.table(T_REPORTS)
            .select("title,html")
            .eq("id", report_id)
            .single()
            .execute()
        )
        return True, res.data
    except Exception as e:
        return False, f"Could not load report: {e}"


def delete_report(report_id):
    return _delete(T_REPORTS, report_id, "report")


# --- Validation rule sets ---------------------------------------------------

def save_rule_set(name, rules):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        payload = {"name": name, "rules": rules}
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user":
            payload["user_id"] = user_id
        client.table(T_RULE_SETS).insert(payload).execute()
        return True, f"Saved rule set '{name}' ({len(rules)} rules)."
    except Exception as e:
        return False, f"Could not save rule set: {e}"


def list_rule_sets():
    client, err = get_client()
    if client is None:
        return False, err
    try:
        query = (
            client.table(T_RULE_SETS)
            .select("id,name,rules,created_at")
            .order("created_at", desc=True)
        )
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user" and not _is_admin():
            query = query.eq("user_id", user_id)
        res = query.execute()
        return True, res.data or []
    except Exception as e:
        return False, f"Could not list rule sets: {e}"


def delete_rule_set(rule_set_id):
    return _delete(T_RULE_SETS, rule_set_id, "rule set")


# --- Saved insights ---------------------------------------------------------

def save_insight(content, dataset_name="", source="ai", confidence_level="", confidence_score=0):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        payload = {
            "content": content,
            "dataset_name": dataset_name or "",
            "source": source or "ai",
            "confidence_level": confidence_level or "",
            "confidence_score": int(confidence_score or 0),
        }
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user":
            payload["user_id"] = user_id
        client.table(T_INSIGHTS).insert(payload).execute()
        return True, "Saved insight."
    except Exception as e:
        return False, f"Could not save insight: {e}"


def list_insights():
    client, err = get_client()
    if client is None:
        return False, err
    try:
        query = (
            client.table(T_INSIGHTS)
            .select("id,dataset_name,source,confidence_level,confidence_score,content,created_at")
            .order("created_at", desc=True)
        )
        user_id = _get_user_id()
        if user_id and user_id != "local-dev-user" and not _is_admin():
            query = query.eq("user_id", user_id)
        res = query.execute()
        return True, res.data or []
    except Exception as e:
        return False, f"Could not list insights: {e}"


def delete_insight(insight_id):
    return _delete(T_INSIGHTS, insight_id, "insight")


# --- Shared helper ----------------------------------------------------------

def _delete(table, row_id, label):
    client, err = get_client()
    if client is None:
        return False, err
    try:
        client.table(table).delete().eq("id", row_id).execute()
        return True, f"Deleted {label}."
    except Exception as e:
        return False, f"Could not delete {label}: {e}"
